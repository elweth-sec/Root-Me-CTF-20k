FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build-env
WORKDIR /app

COPY *.csproj ./
RUN dotnet restore

COPY . ./
RUN dotnet publish -c Release -o out

FROM mcr.microsoft.com/dotnet/aspnet:6.0
WORKDIR /app

COPY --from=build-env /app/out ./

RUN apt update && \
    apt install -y curl wget netcat-traditional ncat

RUN useradd -ms /bin/sh baptiste
RUN chown -R root:root /app

EXPOSE 80

COPY flag_459f0165d7dcbf77f59be4965aa86e99.txt /flag_459f0165d7dcbf77f59be4965aa86e99.txt

USER baptiste

ENTRYPOINT ["dotnet", "CheaterReport.dll"]