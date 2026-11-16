import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Préstamos e Intereses",
    page_icon="💰",
    layout="wide"
)

ARCHIVO_DATOS = "prestamos_db.csv"
FECHA_CORTE_DEFECTO = date(2026, 11, 16)
TASA_SEMANAL = 0.10  # 10% semanal

# Datos iniciales de los 7 clientes
DATOS_INICIALES = [
    {"id": 1, "cliente": "Mariela", "capital": 100.0, "fecha_inicio": "2026-10-19", "estado": "Activo", "notas": "Préstamo inicial"},
    {"id": 2, "cliente": "Yenny", "capital": 250.0, "fecha_inicio": "2026-10-12", "estado": "Activo", "notas": "Préstamo inicial"},
    {"id": 3, "cliente": "Geovanny", "capital": 150.0, "fecha_inicio": "2026-10-26", "estado": "Activo", "notas": "Préstamo inicial"},
    {"id": 4, "cliente": "Alexis 4", "capital": 280.0, "fecha_inicio": "2026-10-05", "estado": "Activo", "notas": "Préstamo inicial"},
    {"id": 5, "cliente": "Chipapa", "capital": 80.0, "fecha_inicio": "2026-11-02", "estado": "Activo", "notas": "Préstamo inicial"},
    {"id": 6, "cliente": "Larry", "capital": 100.0, "fecha_inicio": "2026-10-19", "estado": "Activo", "notas": "Préstamo inicial"},
    {"id": 7, "cliente": "Fabian", "capital": 300.0, "fecha_inicio": "2026-10-12", "estado": "Activo", "notas": "Préstamo inicial"},
]

def cargar_datos() -> pd.DataFrame:
    if not os.path.exists(ARCHIVO_DATOS):
        df = pd.DataFrame(DATOS_INICIALES)
        df.to_csv(ARCHIVO_DATOS, index=False)
        return df
    return pd.read_csv(ARCHIVO_DATOS)

def guardar_datos(df: pd.DataFrame) -> None:
    df.to_csv(ARCHIVO_DATOS, index=False)

def calcular_cartera(df: pd.DataFrame, fecha_corte: date, modo_exacto: bool = False) -> pd.DataFrame:
    resultado = df.copy()
    fechas_inicio = pd.to_datetime(resultado["fecha_inicio"]).dt.date
    dias_transcurridos = fechas_inicio.apply(lambda f: max((fecha_corte - f).days, 0))

    if modo_exacto:
        semanas = (dias_transcurridos / 7.0).round(2)
    else:
        semanas = (dias_transcurridos // 7).astype(int)

    resultado["dias_transcurridos"] = dias_transcurridos
    resultado["semanas"] = semanas
    resultado["interes_semanal"] = (resultado["capital"] * TASA_SEMANAL).round(2)
    resultado["interes_acumulado"] = (resultado["interes_semanal"] * resultado["semanas"]).round(2)
    resultado["saldo_total"] = (resultado["capital"] + resultado["interes_acumulado"]).round(2)
    return resultado

# --- SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.title("🔐 Acceso al Sistema")
        st.caption("Control de Préstamos e Intereses Semanales (10%)")
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            clave = st.text_input("Contraseña", type="password")
            entrar = st.form_submit_button("Iniciar Sesión", use_container_width=True)

            if entrar:
                if usuario == "admin" and clave == "123456":
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
    st.stop()

# --- BARRA LATERAL: CONTROLES Y FILTROS ---
with st.sidebar:
    st.header("⚙️ Parámetros de Cálculo")
    fecha_corte = st.date_input("Fecha de corte", value=FECHA_CORTE_DEFECTO)
    modo_calculo = st.radio(
        "Cálculo de semanas",
        ["Semanas completas", "Prorrateo exacto (días/7)"],
        index=0
    )
    usar_exacto = modo_calculo == "Prorrateo exacto (días/7)"

    st.divider()
    st.header("🔍 Filtros Avanzados")
    df_base = cargar_datos()
    clientes_disponibles = sorted(df_base["cliente"].unique().tolist())
    filtro_clientes = st.multiselect("Filtrar por cliente", options=clientes_disponibles, default=[])
    filtro_estado = st.multiselect("Filtrar por estado", options=["Activo", "Pagado", "Vencido"], default=["Activo", "Vencido"])
    monto_min, monto_max = st.slider(
        "Rango de capital (USD)",
        min_value=0.0,
        max_value=float(max(df_base["capital"].max(), 500.0)),
        value=(0.0, float(max(df_base["capital"].max(), 500.0))),
        step=10.0
    )

    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# --- APLICACIÓN PRINCIPAL ---
st.title("💰 Panel de Control de Préstamos")
st.caption(f"Corte calculado al **{fecha_corte.strftime('%d/%m/%Y')}** | Tasa de interés semanal: **10%**")

df_calculado = calcular_cartera(df_base, fecha_corte, modo_exacto=usar_exacto)

# Aplicar filtros
df_filtrado = df_calculado.copy()
if filtro_clientes:
    df_filtrado = df_filtrado[df_filtrado["cliente"].isin(filtro_clientes)]
if filtro_estado:
    df_filtrado = df_filtrado[df_filtrado["estado"].isin(filtro_estado)]
df_filtrado = df_filtrado[(df_filtrado["capital"] >= monto_min) & (df_filtrado["capital"] <= monto_max)]

# --- MÉTRICAS PRINCIPALES ---
total_capital = df_filtrado["capital"].sum()
total_interes_semanal = df_filtrado["interes_semanal"].sum()
total_interes_acum = df_filtrado["interes_acumulado"].sum()
total_general = df_filtrado["saldo_total"].sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Capital Prestado", f"${total_capital:,.2f}")
m2.metric("Interés Semanal (10%)", f"${total_interes_semanal:,.2f}")
m3.metric("Interés Acumulado", f"${total_interes_acum:,.2f}")
m4.metric("Saldo Total a Cobrar", f"${total_general:,.2f}")

st.divider()

# --- PESTAÑAS DE OPERACIÓN ---
tab_consulta, tab_agregar, tab_modificar = st.tabs([
    "📊 Consulta de Cartera",
    "➕ Agregar Préstamo",
    "✏️ Modificar / Eliminar"
])

with tab_consulta:
    st.subheader("Detalle de Préstamos Filtrados")
    columnas_mostrar = [
        "id", "cliente", "capital", "fecha_inicio", "dias_transcurridos",
        "semanas", "interes_semanal", "interes_acumulado", "saldo_total", "estado", "notas"
    ]
    st.dataframe(
        df_filtrado[columnas_mostrar],
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": "ID",
            "cliente": "Cliente",
            "capital": st.column_config.NumberColumn("Capital", format="$%.2f"),
            "fecha_inicio": "Fecha Inicio",
            "dias_transcurridos": "Días",
            "semanas": "Semanas",
            "interes_semanal": st.column_config.NumberColumn("Interés Semanal", format="$%.2f"),
            "interes_acumulado": st.column_config.NumberColumn("Interés Acumulado", format="$%.2f"),
            "saldo_total": st.column_config.NumberColumn("Saldo Total", format="$%.2f"),
            "estado": "Estado",
            "notas": "Notas"
        }
    )

    csv_export = df_filtrado[columnas_mostrar].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar Reporte en CSV",
        data=csv_export,
        file_name=f"reporte_prestamos_{fecha_corte}.csv",
        mime="text/csv"
    )

with tab_agregar:
    st.subheader("Registrar Nuevo Préstamo")
    with st.form("form_nuevo_prestamo", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        nuevo_cliente = col_a.text_input("Nombre del Cliente")
        nuevo_capital = col_b.number_input("Capital Prestado", min_value=1.0, value=100.0, step=10.0)
        nueva_fecha = col_a.date_input("Fecha de Inicio del Préstamo", value=fecha_corte)
        nuevo_estado = col_b.selectbox("Estado", ["Activo", "Pagado", "Vencido"])
        nuevas_notas = st.text_input("Notas u observaciones")
        guardar_nuevo = st.form_submit_button("Guardar Préstamo")

        if guardar_nuevo:
            if not nuevo_cliente.strip():
                st.warning("Por favor ingresa el nombre del cliente.")
            else:
                nuevo_id = int(df_base["id"].max() + 1) if not df_base.empty else 1
                nuevo_registro = pd.DataFrame([{
                    "id": nuevo_id,
                    "cliente": nuevo_cliente.strip(),
                    "capital": float(nuevo_capital),
                    "fecha_inicio": str(nueva_fecha),
                    "estado": nuevo_estado,
                    "notas": nuevas_notas.strip()
                }])
                df_actualizado = pd.concat([df_base, nuevo_registro], ignore_index=True)
                guardar_datos(df_actualizado)
                st.success(f"Préstamo de {nuevo_cliente} registrado correctamente.")
                st.rerun()

with tab_modificar:
    st.subheader("Editar o Eliminar un Préstamo Existente")
    if df_base.empty:
        st.info("No hay préstamos registrados.")
    else:
        opciones_edicion = {
            f"ID {row['id']} - {row['cliente']} (${row['capital']:,.2f})": row["id"]
            for _, row in df_base.iterrows()
        }
        seleccion = st.selectbox("Selecciona el préstamo a modificar", list(opciones_edicion.keys()))
        id_seleccionado = opciones_edicion[seleccion]
        fila_actual = df_base[df_base["id"] == id_seleccionado].iloc[0]

        with st.form("form_editar_prestamo"):
            c1, c2 = st.columns(2)
            edit_cliente = c1.text_input("Cliente", value=str(fila_actual["cliente"]))
            edit_capital = c2.number_input("Capital", min_value=0.0, value=float(fila_actual["capital"]), step=10.0)
            edit_fecha = c1.date_input(
                "Fecha de Inicio",
                value=datetime.strptime(str(fila_actual["fecha_inicio"]), "%Y-%m-%d").date()
            )
            estados = ["Activo", "Pagado", "Vencido"]
            idx_estado = estados.index(fila_actual["estado"]) if fila_actual["estado"] in estados else 0
            edit_estado = c2.selectbox("Estado", estados, index=idx_estado)
            edit_notas = st.text_input("Notas", value="" if pd.isna(fila_actual["notas"]) else str(fila_actual["notas"]))

            col_btn1, col_btn2 = st.columns(2)
            btn_actualizar = col_btn1.form_submit_button("💾 Guardar Cambios", use_container_width=True)
            btn_eliminar = col_btn2.form_submit_button("🗑️ Eliminar Préstamo", use_container_width=True)

            if btn_actualizar:
                idx = df_base[df_base["id"] == id_seleccionado].index[0]
                df_base.at[idx, "cliente"] = edit_cliente.strip()
                df_base.at[idx, "capital"] = float(edit_capital)
                df_base.at[idx, "fecha_inicio"] = str(edit_fecha)
                df_base.at[idx, "estado"] = edit_estado
                df_base.at[idx, "notas"] = edit_notas.strip()
                guardar_datos(df_base)
                st.success("Cambios guardados exitosamente.")
                st.rerun()

            if btn_eliminar:
                df_base = df_base[df_base["id"] != id_seleccionado]
                guardar_datos(df_base)
                st.warning("Préstamo eliminado.")
                st.rerun()