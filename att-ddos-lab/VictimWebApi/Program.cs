using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using System;
using System.Threading;

var builder = WebApplication.CreateBuilder(args);

// Giới hạn kết nối đồng thời (để quan sát hiệu ứng DDoS)
builder.WebHost.ConfigureKestrel(options =>
{
    options.ListenAnyIP(8080);
    options.Limits.MaxConcurrentConnections = 500;
    options.Limits.MaxConcurrentUpgradedConnections = 500;
    options.Limits.KeepAliveTimeout = TimeSpan.FromSeconds(30);
});

var app = builder.Build();

// Biến đếm request toàn cục
long totalRequests = 0;
long activeRequests = 0;
var startTime = DateTime.UtcNow;

// ==== ENDPOINT CHÍNH (mục tiêu tấn công) ====
app.MapGet("/", async (HttpContext ctx) =>
{
    Interlocked.Increment(ref totalRequests);
    Interlocked.Increment(ref activeRequests);
    try
    {
        // Giả lập xử lý nặng (database query, computation,...)
        await Task.Delay(100); // 100ms delay để dễ bị quá tải
        return Results.Ok(new
        {
            message = "Hello from Victim Web API",
            timestamp = DateTime.UtcNow.ToString("HH:mm:ss.fff"),
            requestId = Guid.NewGuid().ToString("N")[..8]
        });
    }
    finally
    {
        Interlocked.Decrement(ref activeRequests);
    }
});

// ==== ENDPOINT XEM THỐNG KÊ (monitor) ====
app.MapGet("/stats", () =>
{
    var uptime = (DateTime.UtcNow - startTime).TotalSeconds;
    return Results.Ok(new
    {
        status = "running",
        total_requests = Interlocked.Read(ref totalRequests),
        active_requests = Interlocked.Read(ref activeRequests),
        requests_per_second = Math.Round(Interlocked.Read(ref totalRequests) / uptime, 2),
        uptime_seconds = Math.Round(uptime, 1),
        server_time = DateTime.UtcNow.ToString("HH:mm:ss")
    });
});

// ==== ENDPOINT RESET THỐNG KÊ ====
app.MapPost("/reset", () =>
{
    Interlocked.Exchange(ref totalRequests, 0);
    return Results.Ok(new { message = "Stats reset" });
});

Console.WriteLine("=== Victim Web API đang chạy trên port 8080 ===");
Console.WriteLine("   GET  /        -> Endpoint bị tấn công");
Console.WriteLine("   GET  /stats   -> Xem thống kê real-time");
Console.WriteLine("   POST /reset   -> Reset thống kê");

app.Run();
