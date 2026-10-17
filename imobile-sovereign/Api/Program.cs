using System.Security.Claims;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using Npgsql;

var builder = WebApplication.CreateBuilder(args);
var authority = Environment.GetEnvironmentVariable("OIDC_AUTHORITY");
var audience = Environment.GetEnvironmentVariable("OIDC_AUDIENCE");
var connection = Environment.GetEnvironmentVariable("PG_CONNECTION");
if (string.IsNullOrWhiteSpace(authority) || string.IsNullOrWhiteSpace(audience) || string.IsNullOrWhiteSpace(connection))
    throw new InvalidOperationException("Set OIDC_AUTHORITY, OIDC_AUDIENCE, PG_CONNECTION before startup.");
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(o => {
        o.Authority = authority;
        o.Audience = audience;
        o.RequireHttpsMetadata = !builder.Environment.IsDevelopment();
        o.TokenValidationParameters = new TokenValidationParameters {
            ValidateIssuer = true, ValidateAudience = true, ValidateLifetime = true,
            ValidateIssuerSigningKey = true
        };
    });
builder.Services.AddAuthorization();
builder.Services.AddSingleton(NpgsqlDataSource.Create(connection));
var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();
app.MapGet("/health", () => Results.Ok(new { status = "ok", identity_provider = "oidc", records = "postgresql" }));
app.MapGet("/v1/me", (ClaimsPrincipal user) => Results.Ok(new { sub = user.FindFirstValue("sub") })).RequireAuthorization();
app.MapGet("/v1/calls", async (ClaimsPrincipal user, NpgsqlDataSource source, CancellationToken ct) => {
    var owner = user.FindFirstValue("sub");
    if (string.IsNullOrWhiteSpace(owner)) return Results.Unauthorized();
    await using var command = source.CreateCommand(
        "SELECT id,peer_handle,media_kind,call_state,created_at FROM call_records WHERE owner_sub = $1 ORDER BY created_at DESC LIMIT 100");
    command.Parameters.AddWithValue(owner);
    await using var reader = await command.ExecuteReaderAsync(ct);
    var rows = new List<object>();
    while (await reader.ReadAsync(ct))
        rows.Add(new { id = reader.GetGuid(0), peer = reader.GetString(1), kind = reader.GetString(2),
                       status = reader.GetString(3), createdAt = reader.GetDateTime(4) });
    return Results.Ok(rows);
}).RequireAuthorization();
app.MapPost("/v1/calls", async (CallInput data, ClaimsPrincipal user, NpgsqlDataSource source, CancellationToken ct) => {
    var owner = user.FindFirstValue("sub");
    if (string.IsNullOrWhiteSpace(owner)) return Results.Unauthorized();
    if (data.Peer is null || data.Peer.Length is < 1 or > 120 ||
        data.Kind is not ("audio" or "video"))
        return Results.BadRequest(new { error = "Invalid peer or media kind" });
    var id = Guid.NewGuid();
    await using var command = source.CreateCommand(
        "INSERT INTO call_records (id,owner_sub,peer_handle,media_kind,call_state) VALUES ($1,$2,$3,$4,'invited')");
    command.Parameters.AddWithValue(id);
    command.Parameters.AddWithValue(owner);
    command.Parameters.AddWithValue(data.Peer);
    command.Parameters.AddWithValue(data.Kind);
    await command.ExecuteNonQueryAsync(ct);
    return Results.Created($"/v1/calls/{id}", new { id, status = "invited", delivered = false });
}).RequireAuthorization();
app.Run();
record CallInput(string Peer, string Kind);
