using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Newtonsoft.Json;
using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using CheaterReport.Models;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.UseStaticFiles();

app.MapGet("/{*filename}", async context =>
{
    var filename = context.Request.RouteValues["filename"] as string;

    if (string.IsNullOrEmpty(filename))
    {
        filename = "index.html";
    }

    var filePath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", filename);

    if (File.Exists(filePath))
    {
        context.Response.ContentType = "text/html";
        await context.Response.SendFileAsync(filePath);
    }
    else
    {
        context.Response.StatusCode = 404; 
        await context.Response.WriteAsync($"File {filePath} not found.");
    }
});

app.MapPost("/Contact", async context =>
{
    using var reader = new StreamReader(context.Request.Body);
    var json = await reader.ReadToEndAsync();

    try
    {
        dynamic obj = JsonConvert.DeserializeObject<object>(json,
            new JsonSerializerSettings { TypeNameHandling = TypeNameHandling.All }
        );

        var response = new
        {
            success = true
        };
        var responseJson = JsonConvert.SerializeObject(response);
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsync(responseJson);
    }
    catch (Exception ex)
    {
        var response = new
        {
            success = false,
            error = ex.Message
        };
        var responseJson = JsonConvert.SerializeObject(response);
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsync(responseJson);
    }
});

app.Run();