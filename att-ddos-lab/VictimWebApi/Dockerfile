# Dockerfile cho Victim Web API (.NET 9)
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# Copy project file và restore dependencies
COPY VictimWebApi.csproj .
RUN dotnet restore

# Copy source code và build
COPY . .
RUN dotnet publish -c Release -o /app/publish

# Runtime image (nhỏ hơn)
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .

EXPOSE 8080
ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production

ENTRYPOINT ["dotnet", "VictimWebApi.dll"]
