import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. Configuración de la página
st.set_page_config(page_title="Nómina y Turnos", page_icon="⏱️", layout="wide")

# Memoria del sistema para guardar los turnos sin que se borren al recargar
if 'turnos' not in st.session_state:
    st.session_state.turnos = []

st.title("⏱️ Sistema Automático de Nómina por Turnos")
st.markdown("Ingresa tus turnos diarios. El sistema agrupará las semanas, detectará las 42 horas legales y calculará las extras y recargos automáticamente.")
st.divider()

# 2. Datos Básicos
st.header("1. Datos Básicos")
col1, col2 = st.columns(2)
with col1:
    salario_base = st.number_input("Salario Base Mensual ($)", min_value=1300000, step=50000, value=1300000)
with col2:
    auxilio_transporte = st.checkbox("Tiene derecho a Auxilio de Transporte", value=True)

# Valor de la hora ordinaria (Base de 210 horas mensuales por la jornada de 42h)
valor_hora_ordinaria = salario_base / 210

# 3. Registro del Turno Diario
st.header("2. Registro de Asistencia Diario")
with st.form("form_registro"):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        fecha_input = st.date_input("Día de trabajo")
    with c2:
        e1 = st.time_input("Entrada Mañana", value=datetime.strptime("07:00", "%H:%M").time())
    with c3:
        s1 = st.time_input("Salida Mañana", value=datetime.strptime("12:00", "%H:%M").time())
    with c4:
        e2 = st.time_input("Entrada Tarde", value=datetime.strptime("14:00", "%H:%M").time())
    with c5:
        s2 = st.time_input("Salida Tarde", value=datetime.strptime("19:00", "%H:%M").time())
    
    es_festivo = st.checkbox("¿Es un día Festivo? (Los domingos el sistema los detecta solo)")
    
    submit = st.form_submit_button("Guardar Turno del Día")
    
    if submit:
        # Calcular duración de los turnos
        t_e1 = datetime.combine(fecha_input, e1)
        t_s1 = datetime.combine(fecha_input, s1)
        t_e2 = datetime.combine(fecha_input, e2)
        t_s2 = datetime.combine(fecha_input, s2)
        
        horas_m = (t_s1 - t_e1).total_seconds() / 3600
        horas_t = (t_s2 - t_e2).total_seconds() / 3600
        total_horas_dia = horas_m + horas_t
        
        # Detectar si es domingo matemáticamente (0 es Lunes, 6 es Domingo)
        es_domingo = (fecha_input.weekday() == 6)
        
        # Guardar en la memoria
        st.session_state.turnos.append({
            "Fecha": fecha_input,
            "Semana del Año": fecha_input.isocalendar()[1], # Agrupa por semana
            "Día": fecha_input.strftime("%A"),
            "Horas Trabajadas": total_horas_dia,
            "Es Domingo/Festivo": es_domingo or es_festivo
        })
        st.success(f"✅ ¡Turno guardado! Trabajaste {total_horas_dia} horas este día.")

# 4. Tabla y Cálculos Automáticos
if len(st.session_state.turnos) > 0:
    st.header("3. Base de Datos del Mes")
    df = pd.DataFrame(st.session_state.turnos)
    
    # Mostrar la tabla en pantalla
    st.dataframe(df, use_container_width=True)
    
    # --- NUEVO: Módulo para borrar registros específicos ---
    st.markdown("### 🛠️ Editar Registros")
    col_borrar1, col_borrar2 = st.columns([3, 1])
    
    with col_borrar1:
        # Crea una lista de opciones para que sepas qué vas a borrar
        opciones_borrar = [f"Fila {i}: Día {t['Fecha']} (Trabajó {t['Horas Trabajadas']:.2f} hrs)" for i, t in enumerate(st.session_state.turnos)]
        seleccion_borrar = st.selectbox("Selecciona el turno que te quedó mal:", opciones_borrar)
        
    with col_borrar2:
        st.write("") # Espaciado visual para alinear el botón
        st.write("")
        if st.button("🗑️ Borrar SOLO este turno"):
            # Extrae el número de la fila y la elimina de la memoria
            indice = int(seleccion_borrar.split(":")[0].replace("Fila ", ""))
            st.session_state.turnos.pop(indice)
            st.rerun() # Recarga la página automáticamente

    if st.button("🚨 Borrar TODOS los registros"):
        st.session_state.turnos = []
        st.rerun()

    # --- EL CEREBRO MATEMÁTICO ---
    horas_ordinarias = 0
    horas_extras = 0
    horas_dom_fest = 0
    
    # Agrupar por semanas para aplicar la ley de 42 horas
    for semana, grupo in df.groupby("Semana del Año"):
        horas_semana = grupo["Horas Trabajadas"].sum()
        
        # Lógica de Horas Extras semanales
        if horas_semana > 42:
            horas_ordinarias += 42
            horas_extras += (horas_semana - 42)
        else:
            horas_ordinarias += horas_semana
            
        # Sumar recargos dominicales (si aplica en la semana)
        horas_dom_fest += grupo[grupo["Es Domingo/Festivo"] == True]["Horas Trabajadas"].sum()

    # Traducir horas a dinero
    pago_ordinario = horas_ordinarias * valor_hora_ordinaria
    pago_extras = horas_extras * (valor_hora_ordinaria * 1.25) # Extra diurna legal (+25%)
    pago_dom_fest = horas_dom_fest * (valor_hora_ordinaria * 0.75) # Recargo Dominical (+75%)
    
    total_ganado = pago_ordinario + pago_extras + pago_dom_fest
    
    # Transporte proporcional a los días que fue a trabajar
    dias_trabajados = len(df)
    aux_transporte = (162000 / 30) * dias_trabajados if auxilio_transporte else 0
    
    # Descuentos
    salud = total_ganado * 0.04
    pension = total_ganado * 0.04
    neto_pagar = (total_ganado + aux_transporte) - salud - pension

    # 5. El Recibo Final (Lo que querías mantener)
    st.header("4. Recibo de Pago Estimado")
    st.success(f"### 💵 Total Neto a Recibir: ${neto_pagar:,.0f}")
    
    with st.expander("Ver desglose detallado de la nómina (Clic para expandir)"):
        st.write(f"**Días Registrados:** {dias_trabajados} días")
        st.write(f"**Horas Ordinarias (Legal 42h/sem):** {horas_ordinarias:,.1f} h = ${pago_ordinario:,.0f}")
        st.write(f"**Horas Extras Semanales:** {horas_extras:,.1f} h = ${pago_extras:,.0f}")
        st.write(f"**Horas Dominicales/Festivas:** {horas_dom_fest:,.1f} h = ${pago_dom_fest:,.0f}")
        st.write(f"**Auxilio de Transporte:** ${aux_transporte:,.0f}")
        st.write("---")
        st.write(f"**Deducción Salud (4%):** -${salud:,.0f}")
        st.write(f"**Deducción Pensión (4%):** -${pension:,.0f}")