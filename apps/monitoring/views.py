# apps/monitoring/views.py
import time
from datetime import datetime

import psutil
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from prometheus_client import Counter, Gauge, Histogram
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

# ─────────────────────────────────────────────────
# Prometheus Metrics
# ─────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "django_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "environment"],
)
REQUEST_LATENCY = Histogram(
    "django_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)
DB_QUERY_COUNT = Counter(
    "django_db_queries_total",
    "Total DB queries",
    ["operation"],
)
ACTIVE_USERS = Gauge(
    "django_active_users",
    "Currently active users",
    ["tenant"],
)
CELERY_TASKS = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"],
)


# ─────────────────────────────────────────────────
# Health Check Endpoint
# ─────────────────────────────────────────────────
@never_cache
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Comprehensive health check endpoint.
    Returns 200 if all subsystems are healthy.
    """
    checks = {}
    overall_status = "healthy"
    http_status = 200

    # Database check
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_latency = round((time.time() - start) * 1000, 2)
        checks["database"] = {"status": "healthy", "latency_ms": db_latency}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"
        http_status = 503

    # Cache (Redis) check
    try:
        start = time.time()
        cache.set("health_check_key", "ok", timeout=10)
        val = cache.get("health_check_key")
        cache_latency = round((time.time() - start) * 1000, 2)
        if val == "ok":
            checks["cache"] = {"status": "healthy", "latency_ms": cache_latency}
        else:
            checks["cache"] = {"status": "degraded"}
            overall_status = "degraded"
    except Exception as e:
        checks["cache"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"
        http_status = 503

    # Disk check
    disk = psutil.disk_usage("/")
    disk_percent = disk.percent
    checks["disk"] = {
        "status": "healthy" if disk_percent < 85 else "warning",
        "used_percent": disk_percent,
        "free_gb": round(disk.free / (1024**3), 2),
    }
    if disk_percent >= 90:
        overall_status = "degraded"

    # Memory check
    mem = psutil.virtual_memory()
    checks["memory"] = {
        "status": "healthy" if mem.percent < 85 else "warning",
        "used_percent": mem.percent,
        "available_mb": round(mem.available / (1024**2), 2),
    }

    return JsonResponse(
        {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": request.META.get("ENVIRONMENT", "unknown"),
            "checks": checks,
        },
        status=http_status,
    )


# ─────────────────────────────────────────────────
# Server Metrics Endpoint
# ─────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAdminUser])
def server_metrics(request):
    """Return real-time server metrics."""
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net_io = psutil.net_io_counters()

    return Response(
        {
            "cpu": {
                "overall_percent": sum(cpu_percent) / len(cpu_percent),
                "per_core": cpu_percent,
                "core_count": psutil.cpu_count(),
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            },
            "network": {
                "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# ─────────────────────────────────────────────────
# Database Metrics Endpoint
# ─────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAdminUser])
def db_metrics(request):
    """Return database performance metrics."""
    with connection.cursor() as cursor:
        # Active connections
        cursor.execute("""
            SELECT count(*) FROM pg_stat_activity
            WHERE state = 'active'
        """)
        active_connections = cursor.fetchone()[0]

        # Database size
        cursor.execute("""
            SELECT pg_database_size(current_database())
        """)
        db_size_bytes = cursor.fetchone()[0]

        # Slow queries (last 10)
        cursor.execute("""
            SELECT query, calls, mean_exec_time, rows
            FROM pg_stat_statements
            ORDER BY mean_exec_time DESC
            LIMIT 10
        """)
        try:
            slow_queries = [
                {
                    "query": row[0][:200],
                    "calls": row[1],
                    "mean_exec_time_ms": round(row[2], 2),
                    "rows": row[3],
                }
                for row in cursor.fetchall()
            ]
        except Exception:
            slow_queries = []

        # Table stats
        cursor.execute("""
            SELECT relname, n_live_tup, n_dead_tup, last_vacuum, last_analyze
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
            LIMIT 20
        """)
        table_stats = [
            {
                "table": row[0],
                "live_rows": row[1],
                "dead_rows": row[2],
                "last_vacuum": str(row[3]),
                "last_analyze": str(row[4]),
            }
            for row in cursor.fetchall()
        ]

    return Response(
        {
            "active_connections": active_connections,
            "db_size_mb": round(db_size_bytes / (1024**2), 2),
            "slow_queries": slow_queries,
            "table_stats": table_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# ─────────────────────────────────────────────────
# Multi-tenant Usage Endpoint
# ─────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAdminUser])
def tenant_metrics(request):
    """Return per-tenant usage metrics."""
    from django.contrib.auth import get_user_model

    from apps.tenants.models import Tenant

    User = get_user_model()
    tenants = Tenant.objects.all().values("id", "name", "schema_name", "created_on")

    tenant_data = []
    for tenant in tenants:
        user_count = User.objects.filter(
            # Adjust filter based on your tenant model
        ).count()
        tenant_data.append(
            {
                "id": str(tenant["id"]),
                "name": tenant["name"],
                "schema": tenant["schema_name"],
                "created_on": str(tenant["created_on"]),
                "user_count": user_count,
            }
        )

    return Response(
        {
            "total_tenants": len(tenant_data),
            "tenants": tenant_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
