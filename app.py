import streamlit as st

st.markdown(
    """
    <style>
    /* Fondo del contenido principal */
    .stApp {
        background-color: #000000;
    }
    
    /* Fondo de la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #000000;
    }
    
    /* Fondo de la barra superior (cabecera) */
    header[data-testid="stHeader"] {
        background-color: #000000;
    }
    </style>
    """,
    unsafe_allow_html=True
)

import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import os

st.set_page_config(
    page_title="David López - Gestión Financiera",
    page_icon="💼",
    layout="wide"
)

# Función helper para formatear a Moneda Colombiana (COP)
def formato_cop(valor):
    try:
        return f"${int(round(float(valor))):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "$0"

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Cargar datos
def cargar_atenciones():
    try:
        df = conn.read(worksheet="atenciones", ttl="0s")
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame(columns=["id", "fecha", "clienta", "servicio", "monto"])

def cargar_deudas():
    try:
        df = conn.read(worksheet="deudas", ttl="0s")
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame(columns=["id", "acreedor", "monto_total", "cuotas_totales", "cuotas_pagadas", "valor_cuota", "estado", "tipo"])

# Mostrar Logo y Título
st.title("Gestor Financiero - David López")

st.markdown("---")

# Menú lateral
opcion = st.sidebar.radio(
    "Navegación",
    ["Registrar Atención", "Historial e Ingresos", "Deudas y Balance General"]
)

# --- OPCIÓN 1: REGISTRAR ATENCIÓN ---
if opcion == "Registrar Atención":
    st.header("📝 Registrar Nueva Atención")
    
    with st.form("form_atencion", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            clienta = st.text_input("Nombre de la Clienta:", placeholder="Ej. María López")
            servicio = st.text_input("Servicio Realizado:", placeholder="Ej. Semipermanente + Acrílico")
        with col2:
            monto = st.number_input("Monto Cobrado ($ COP):", min_value=0.0, step=1000.0, format="%.0f")
        
        guardar = st.form_submit_button("💾 Guardar Atención", use_container_width=True)

    if guardar:
        if not clienta or not servicio or monto <= 0:
            st.error("Por favor completa todos los campos con un monto válido.")
        else:
            df_existing = cargar_atenciones()
            nuevo_id = 1 if df_existing.empty else int(df_existing["id"].max()) + 1
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            nuevo_registro = pd.DataFrame([{
                "id": nuevo_id,
                "fecha": fecha_actual,
                "clienta": clienta,
                "servicio": servicio,
                "monto": monto
            }])
            
            df_updated = pd.concat([df_existing, nuevo_registro], ignore_index=True)
            conn.update(worksheet="atenciones", data=df_updated)
            st.success(f"¡Atención guardada en la nube para {clienta} por {formato_cop(monto)}!")

# --- OPCIÓN 2: HISTORIAL E INGRESOS ---
elif opcion == "Historial e Ingresos":
    st.header("📊 Historial de Ingresos")
    
    df = cargar_atenciones()

    if not df.empty:
        df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0)
        df["fecha"] = df["fecha"].astype(str)
        df = df.sort_values(by="id", ascending=False)

        hoy_str = datetime.now().strftime("%Y-%m-%d")
        mes_str = datetime.now().strftime("%Y-%m")

        total_hoy = df[df['fecha'].str.startswith(hoy_str)]['monto'].sum()
        total_mes = df[df['fecha'].str.startswith(mes_str)]['monto'].sum()
        total_acumulado = df['monto'].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Ingresos Hoy", formato_cop(total_hoy))
        m2.metric("Ingresos Este Mes", formato_cop(total_mes))
        m3.metric("Total Acumulado", formato_cop(total_acumulado))

        st.subheader("Tabla de Registros")
        
        df_mostrar = df.copy()
        df_mostrar["monto"] = df_mostrar["monto"].apply(formato_cop)
        st.dataframe(df_mostrar, use_container_width=True)

        st.markdown("---")
        st.subheader("🛠️ Administrar / Eliminar Registros")
        
        col_del, col_edit = st.columns(2)

        with col_del:
            st.markdown("##### ❌ Eliminar Registro Error")
            id_eliminar = st.number_input("ID a Eliminar:", min_value=1, step=1, key="del_id")
            if st.button("🗑️ Borrar Servicio", use_container_width=True):
                df_filtrado = df[df["id"] != id_eliminar]
                conn.update(worksheet="atenciones", data=df_filtrado)
                st.success(f"Registro ID {id_eliminar} eliminado permanentemente.")
                st.rerun()

        with col_edit:
            st.markdown("##### ✏️ Editar Registro")
            id_editar = st.number_input("ID a Modificar:", min_value=1, step=1, key="edit_id")
            row_edit = df[df["id"] == id_editar]

            if not row_edit.empty:
                r = row_edit.iloc[0]
                c_edit = st.text_input("Clienta:", value=str(r["clienta"]))
                s_edit = st.text_input("Servicio:", value=str(r["servicio"]))
                m_edit = st.number_input("Monto ($ COP):", value=float(r["monto"]), step=1000.0)

                if st.button("💾 Actualizar Registro", use_container_width=True):
                    df.loc[df["id"] == id_editar, ["clienta", "servicio", "monto"]] = [c_edit, s_edit, m_edit]
                    conn.update(worksheet="atenciones", data=df)
                    st.success(f"Registro ID {id_editar} actualizado.")
                    st.rerun()
            else:
                st.info("Ingresa un ID válido para editar.")
    else:
        st.info("Aún no hay atenciones registradas.")

# --- OPCIÓN 3: DEUDAS Y BALANCE GENERAL ---
elif opcion == "Deudas y Balance General":
    st.header("⚖️ Control de Deudas y Balance General")
    
    df_atenciones = cargar_atenciones()
    
    # Calcular ingresos de este mes
    if not df_atenciones.empty:
        df_atenciones["monto"] = pd.to_numeric(df_atenciones["monto"], errors="coerce").fillna(0)
        df_atenciones["fecha"] = df_atenciones["fecha"].astype(str)
        mes_str = datetime.now().strftime("%Y-%m")
        ingresos_mes = df_atenciones[df_atenciones['fecha'].str.startswith(mes_str)]['monto'].sum()
    else:
        ingresos_mes = 0.0

    df_deudas = cargar_deudas()

    if not df_deudas.empty:
        df_deudas["monto_total"] = pd.to_numeric(df_deudas["monto_total"], errors="coerce").fillna(0)
        df_deudas["cuotas_totales"] = pd.to_numeric(df_deudas["cuotas_totales"], errors="coerce").fillna(1)
        df_deudas["cuotas_pagadas"] = pd.to_numeric(df_deudas["cuotas_pagadas"], errors="coerce").fillna(0)
        df_deudas["valor_cuota"] = pd.to_numeric(df_deudas["valor_cuota"], errors="coerce").fillna(0)
        
        df_deudas['monto_pagado'] = df_deudas['cuotas_pagadas'] * df_deudas['valor_cuota']
        df_deudas['saldo_pendiente'] = df_deudas['monto_total'] - df_deudas['monto_pagado']
        
        # Deudas pendientes activas
        deudas_pendientes = df_deudas[df_deudas['estado'] == 'PENDIENTE']
        
        # Compromiso mensual (suma únicamente los valores de la cuota del mes de todas las deudas activas)
        compromisos_mes = deudas_pendientes['valor_cuota'].sum()
        total_deuda_acumulada = deudas_pendientes['saldo_pendiente'].sum()
    else:
        compromisos_mes = 0.0
        total_deuda_acumulada = 0.0

    # Balance Neto Mensual = Ingresos de este Mes - Cuotas a pagar este Mes
    balance_neto_mes = ingresos_mes - compromisos_mes

    b1, b2, b3 = st.columns(3)
    b1.metric("Ingresos Este Mes", formato_cop(ingresos_mes))
    b2.metric("Compromisos del Mes (Cuotas/Servicios)", formato_cop(compromisos_mes), help=f"Total acumulado a pagar en el tiempo: {formato_cop(total_deuda_acumulada)}")
    
    if balance_neto_mes >= 0:
        b3.metric("Balance del Mes", formato_cop(balance_neto_mes), delta="POSITIVO 🟢")
    else:
        b3.metric("Balance del Mes", f"-{formato_cop(abs(balance_neto_mes))}", delta="-DÉFICIT 🔴", delta_color="inverse")

    st.markdown("---")

    col_form, col_tabla = st.columns([1, 1.5])

    with col_form:
        st.subheader("Registrar Deuda / Servicio")
        
        tipo_deuda = st.radio(
            "Tipo de Obligación:",
            ["Deuda a Cuotas", "Recurrente Mensual (Ej. Celular)"],
            horizontal=True
        )
        
        with st.form("form_deuda", clear_on_submit=True):
            acreedor = st.text_input("A quién / qué servicio le debe:", placeholder="Ej. Proveedor o Plan Celular")
            
            if tipo_deuda == "Deuda a Cuotas":
                monto_deuda = st.number_input("Monto Total ($ COP):", min_value=0.0, step=10000.0)
                cuotas = st.number_input("Número de Cuotas:", min_value=1, step=1, value=1)
            else:
                monto_deuda = st.number_input("Valor Mensual Fijo ($ COP):", min_value=0.0, step=5000.0)
                cuotas = 999  # Marca para servicios recurrentes de pago continuo
                
            guardar_d = st.form_submit_button("📌 Registrar Obligación", use_container_width=True)

        if guardar_d:
            if not acreedor or monto_deuda <= 0:
                st.error("Completa los datos correctamente.")
            else:
                nuevo_id = 1 if df_deudas.empty else int(df_deudas["id"].max()) + 1
                
                if tipo_deuda == "Deuda a Cuotas":
                    valor_cuota = monto_deuda / cuotas
                    monto_total_reg = monto_deuda
                else:
                    valor_cuota = monto_deuda
                    monto_total_reg = monto_deuda  # Para recurrentes el total del registro base es el mes
                
                nueva_deuda = pd.DataFrame([{
                    "id": nuevo_id,
                    "acreedor": acreedor,
                    "monto_total": monto_total_reg,
                    "cuotas_totales": cuotas,
                    "cuotas_pagadas": 0,
                    "valor_cuota": valor_cuota,
                    "estado": "PENDIENTE",
                    "tipo": tipo_deuda
                }])
                
                df_updated_deudas = pd.concat([df_deudas, nueva_deuda], ignore_index=True)
                conn.update(worksheet="deudas", data=df_updated_deudas)
                st.success(f"Registrado exitosamente para {acreedor}.")
                st.rerun()

        st.subheader("Abonar Cuota / Servicio")
        with st.form("form_abono", clear_on_submit=True):
            id_deuda = st.number_input("ID de Deuda / Servicio:", min_value=1, step=1)
            pagar_c = st.form_submit_button("💳 Registrar Pago de 1 Mes/Cuota", use_container_width=True)

        if pagar_c:
            if not df_deudas.empty and id_deuda in df_deudas["id"].values:
                row_idx = df_deudas[df_deudas["id"] == id_deuda].index[0]
                c_tot = df_deudas.loc[row_idx, "cuotas_totales"]
                c_pag = df_deudas.loc[row_idx, "cuotas_pagadas"]

                if c_tot != 999 and c_pag >= c_tot:
                    st.info("Esta deuda a cuotas ya está cancelada en su totalidad.")
                else:
                    nuevas_pag = c_pag + 1
                    estado = "PAGADA" if (c_tot != 999 and nuevas_pag == c_tot) else "PENDIENTE"
                    
                    df_deudas.loc[row_idx, ["cuotas_pagadas", "estado"]] = [nuevas_pag, estado]
                    conn.update(worksheet="deudas", data=df_deudas)
                    st.success(f"¡Pago de cuota/servicio registrado con éxito!")
                    st.rerun()
            else:
                st.error("No existe un registro con ese ID.")

    with col_tabla:
        st.subheader("Listado de Obligaciones")
        if not df_deudas.empty:
            df_tabla_deudas = df_deudas.copy()
            
            # Reemplazar el número 999 de cuotas por el texto "Recurrente"
            df_tabla_deudas["cuotas_totales"] = df_tabla_deudas["cuotas_totales"].apply(
                lambda x: "Recurrente" if str(x) == "999" else x
            )
            
            # Formatear montos a pesos colombianos
            df_tabla_deudas["valor_cuota"] = df_tabla_deudas["valor_cuota"].apply(formato_cop)
            df_tabla_deudas["saldo_pendiente"] = df_tabla_deudas["saldo_pendiente"].apply(formato_cop)
            
            st.dataframe(
                df_tabla_deudas[['id', 'acreedor', 'cuotas_pagadas', 'cuotas_totales', 'valor_cuota', 'saldo_pendiente', 'estado']],
                use_container_width=True
            )
        else:
            st.info("No hay deudas o servicios registrados.")