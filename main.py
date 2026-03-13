import os
import sqlite3
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- 1. CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "facturas.db")

class Factura(BaseModel):
    cliente: str = Field(..., min_length=3)
    nit_cc: str
    monto_subtotal: float = Field(..., gt=0)
    iva_porcentaje: float = Field(0.19, ge=0, le=1)

def conectar_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_tabla():
    with conectar_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                cliente TEXT,
                nit_cc TEXT,
                subtotal REAL,
                iva_porcentaje REAL,
                valor_iva REAL,
                total REAL
            )
        """)

inicializar_tabla()

app = FastAPI(title="Sistema de Facturación SQL")

# --- NUEVO: CONFIGURACIÓN DE CORS (Indispensable para el index.html) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. ENDPOINTS ---

@app.get("/", tags=["Inicio"])
def inicio():
    return {"mensaje": "Servidor Funcionando", "db": DB_PATH}

@app.get("/facturas", tags=["Facturas"])
def listar_facturas():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facturas")
        return [dict(f) for f in cursor.fetchall()]

@app.post("/facturas", tags=["Facturas"])
def crear_factura(factura: Factura):
    # 1. Realizar cálculos
    valor_iva = round(factura.monto_subtotal * factura.iva_porcentaje, 2)
    total_pagar = round(factura.monto_subtotal + valor_iva, 2)
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # 2. Conectar e Insertar en la DB
        with conectar_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO facturas (fecha, cliente, nit_cc, subtotal, iva_porcentaje, valor_iva, total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fecha_hoy, factura.cliente, factura.nit_cc, factura.monto_subtotal, 
                  factura.iva_porcentaje, valor_iva, total_pagar))
            
            conn.commit() # Asegura que se guarden los cambios
            
        return {"mensaje": "Factura guardada", "total": total_pagar}
    
    except Exception as e:
        print(f"Error en DB: {e}")
        raise HTTPException(status_code=500, detail="Error interno al guardar en base de datos")