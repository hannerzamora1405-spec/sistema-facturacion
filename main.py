import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 1. DEFINIR LA APP UNA SOLA VEZ
app = FastAPI(title="Sistema de Facturación SQL")

# 2. CONFIGURAR CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- CONFIGURACIÓN DE DB ---
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

# --- 1. En inicializar_tabla añade la columna 'activa' ---
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
                total REAL,
                activa INTEGER DEFAULT 1  -- 1 para activa, 0 para "borrada"
            )
        """)

# --- 2. En listar_facturas, filtramos las activas ---
@app.get("/facturas", tags=["Facturas"])
def listar_facturas():
    with conectar_db() as conn:
        cursor = conn.cursor()
        # Solo traemos las que no han sido borradas lógicamente
        cursor.execute("SELECT * FROM facturas WHERE activa = 1")
        return [dict(f) for f in cursor.fetchall()]

# --- 3. Modificamos el endpoint DELETE ---
@app.delete("/facturas/{factura_id}", tags=["Facturas"])
def eliminar_factura(factura_id: int):
    with conectar_db() as conn:
        cursor = conn.cursor()
        # En lugar de borrar, desactivamos
        cursor.execute("UPDATE facturas SET activa = 0 WHERE id = ?", (factura_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
    return {"mensaje": f"Factura {factura_id} desactivada (borrado lógico)"}