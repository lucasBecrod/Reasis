#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONFIGURACIÓN GEMINI API - Gestión segura de claves API
IMPORTANTE: Este archivo contiene claves API sensibles - mantener seguro
"""

# API Keys Gemini - CONFIDENCIAL
GEMINI_KEYS = {
    "primary": {
        "key": "AIzaSyDi8ggbQO_dbDoWUj2rGbkHLjyPfGZ16nU",
        "description": "API Key principal - Nueva quota completa",
        "status": "active",
        "daily_limit": 50
    },
    "backup": {
        "key": "AIzaSyDqSlwH1rDtRGatRquZX6WVK0cM28Y38z0", 
        "description": "API Key backup - Para failover",
        "status": "active",
        "daily_limit": 50
    }
}

# Endpoints Gemini
GEMINI_MODEL = "gemini-2.0-flash-exp"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

def get_endpoint(api_key: str) -> str:
    """Construye endpoint completo para una API key"""
    return f"{GEMINI_BASE_URL}/{GEMINI_MODEL}:generateContent?key={api_key}"

def get_primary_config():
    """Retorna configuración de API primaria"""
    primary = GEMINI_KEYS["primary"]
    return {
        "key": primary["key"],
        "endpoint": get_endpoint(primary["key"]),
        "description": primary["description"]
    }

def get_backup_config():
    """Retorna configuración de API backup"""
    backup = GEMINI_KEYS["backup"]
    return {
        "key": backup["key"],
        "endpoint": get_endpoint(backup["key"]),
        "description": backup["description"]
    }

def mostrar_estado_apis():
    """Muestra estado actual de las APIs"""
    print("=== ESTADO APIS GEMINI ===")
    for nombre, config in GEMINI_KEYS.items():
        key_preview = config["key"][:20] + "..."
        print(f"{nombre.upper()}:")
        print(f"  Key: {key_preview}")
        print(f"  Status: {config['status']}")
        print(f"  Limit: {config['daily_limit']} requests/día")
        print(f"  Descripción: {config['description']}")
        print()

if __name__ == "__main__":
    mostrar_estado_apis()
    
    print("=== CONFIGURACIÓN LISTA ===")
    print("Primary endpoint:", get_primary_config()["endpoint"])
    print("Backup endpoint:", get_backup_config()["endpoint"])