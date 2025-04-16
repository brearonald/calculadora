import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

st.set_page_config(page_title="Calculadora de Trading Multiactivo", layout="wide")
st.title("🎯 Calculadora de Trading Multiactivo con Gestión de Riesgos")

# Definimos CSS personalizado para los sliders
st.markdown("""
<style>
    /* Estilo para el slider de Stop Loss (rojo) */
    div[data-testid="stSlider"] > div:has(div[aria-valuemin][aria-valuemax][aria-valuenow]:has(div > div:has(div:has(span:has(div:has(div:has(strong:contains("Precio SL")))))))) > div:nth-child(2) {
        background: linear-gradient(to right, #cf0000, #ff5f5f) !important;
    }
    
    /* Estilo para el slider de Take Profit (verde) */
    div[data-testid="stSlider"] > div:has(div[aria-valuemin][aria-valuemax][aria-valuenow]:has(div > div:has(div:has(span:has(div:has(div:has(strong:contains("Precio TP")))))))) > div:nth-child(2) {
        background: linear-gradient(to right, #00b300, #92d050) !important;
    }
</style>
""", unsafe_allow_html=True)

ticker_colors = {
    "AAPL": "#1f77b4",  # muted blue
    "GOOG": "#ff7f0e",  # safety orange
    "TSLA": "#2ca02c",  # cooked asparagus green
    "DEFAULT": "#d62728" # brick red
}

def analyze_ticker(default_ticker, column_index):
    ticker_key = f"ticker_input_{column_index}"
    precio_usuario_key = f"precio_usuario_{column_index}"

    if ticker_key not in st.session_state:
        st.session_state[ticker_key] = default_ticker
    if precio_usuario_key not in st.session_state:
        st.session_state[precio_usuario_key] = 0.0

    # --- Functions (ticker-specific) ---
    def obtener_precio_actual(ticker_str):
        try:
            ticker = yf.Ticker(ticker_str)
            hist = ticker.history(period="1d")
            return hist.iloc[-1]['Close'] if not hist.empty else 0.0
        except:
            return 0.0

    def actualizar_precio_usuario(ticker_index):
        current_ticker = st.session_state[f"ticker_input_{ticker_index}"]
        st.session_state[f"precio_usuario_{ticker_index}"] = obtener_precio_actual(current_ticker)
    
    # Función para determinar el formato correcto según el precio
    def get_price_format(price):
        if price < 1:
            return "%.2f"  # Para penny stocks: 0.30
        elif price < 10:  
            return "%.2f"  # Para precios bajos: 4.50
        elif price < 100:
            return "%.2f"  # Para precios medios: 10.30
        else:
            return "%.2f"  # Para precios altos: 120.30

    # Función para sincronizar el valor del slider con el input manual
    def sync_sl_slider(column_index):
        st.session_state[f"sl_slider_{column_index}"] = st.session_state[f"sl_manual_{column_index}"]
        
    def sync_sl_manual(column_index):
        st.session_state[f"sl_manual_{column_index}"] = st.session_state[f"sl_slider_{column_index}"]
        
    def sync_tp_slider(column_index):
        st.session_state[f"tp_slider_{column_index}"] = st.session_state[f"tp_manual_{column_index}"]
        
    def sync_tp_manual(column_index):
        st.session_state[f"tp_manual_{column_index}"] = st.session_state[f"tp_slider_{column_index}"]

    # --- Input Widgets ---
    ticker = st.text_input(f"Ticker", st.session_state[ticker_key], key=ticker_key, on_change=lambda idx=column_index: actualizar_precio_usuario(idx)).upper()
    ticker_color = ticker_colors.get(ticker, ticker_colors["DEFAULT"])
    st.markdown(f"<h3 style='color: {ticker_color};'>{ticker.upper()}</h3>", unsafe_allow_html=True)

    current_price_slider = obtener_precio_actual(ticker)
    price_format = get_price_format(current_price_slider)
    step_size = 0.01  # Step size fijo de 0.01 (centavo a centavo)
    
    st.markdown(f"**Precio actual de mercado:** ${current_price_slider:{price_format[1:]}}")

    precio_usuario = st.number_input(
        "Precio base de entrada (Manual):",
        min_value=0.01,
        value=max(0.01, st.session_state[precio_usuario_key]),
        step=step_size,
        format=price_format,
        key=f"precio_manual_{column_index}"
    )
    st.session_state[precio_usuario_key] = precio_usuario

    tipo_operacion = st.radio("Tipo de Operación:", ("Long (Comprar)", "Short (Vender)"), key=f"tipo_op_{column_index}")

    # Cálculo de valores por defecto para SL y TP
    default_sl = current_price_slider * 0.98 if current_price_slider > 0 else precio_usuario * 0.98
    default_tp = current_price_slider * 1.02 if current_price_slider > 0 else precio_usuario * 1.02
    
    # Asegurarse de que los valores sean al menos 0.01
    default_sl = max(0.01, default_sl)
    default_tp = max(0.01, default_tp)
    
    # IMPORTANTE: Inicializar los valores de sesión antes de calcular los rangos
    if f"sl_slider_{column_index}" not in st.session_state:
        st.session_state[f"sl_slider_{column_index}"] = float(default_sl)
    if f"sl_manual_{column_index}" not in st.session_state:
        st.session_state[f"sl_manual_{column_index}"] = float(default_sl)
    if f"tp_slider_{column_index}" not in st.session_state:
        st.session_state[f"tp_slider_{column_index}"] = float(default_tp)
    if f"tp_manual_{column_index}" not in st.session_state:
        st.session_state[f"tp_manual_{column_index}"] = float(default_tp)
    
    # Calculamos rangos adecuados para los sliders basados en el tipo de operación
    if tipo_operacion == "Long (Comprar)":
        sl_min = max(0.01, precio_usuario * 0.80)
        sl_max = max(0.02, precio_usuario * 0.99)
        tp_min = max(0.01, precio_usuario * 1.01)
        tp_max = max(0.02, precio_usuario * 1.20)
    else:  # Short
        sl_min = max(0.01, precio_usuario * 1.01)
        sl_max = max(0.02, precio_usuario * 1.20)
        tp_min = max(0.01, precio_usuario * 0.80)
        tp_max = max(0.02, precio_usuario * 0.99)
    
    # Ajustar los valores de la sesión dentro de los rangos si es necesario
    st.session_state[f"sl_slider_{column_index}"] = max(sl_min, min(sl_max, st.session_state[f"sl_slider_{column_index}"]))
    st.session_state[f"sl_manual_{column_index}"] = max(sl_min, min(sl_max, st.session_state[f"sl_manual_{column_index}"]))
    st.session_state[f"tp_slider_{column_index}"] = max(tp_min, min(tp_max, st.session_state[f"tp_slider_{column_index}"]))
    st.session_state[f"tp_manual_{column_index}"] = max(tp_min, min(tp_max, st.session_state[f"tp_manual_{column_index}"]))
        
    # Sliders y campos manuales para SL y TP
    st.subheader("🛑 Stop Loss")
    col_sl_slider, col_sl_manual = st.columns([3, 1])
    
    with col_sl_slider:
        precio_stop = st.slider(
            "Precio SL", 
            min_value=float(sl_min), 
            max_value=float(sl_max), 
            value=st.session_state[f"sl_slider_{column_index}"],
            step=step_size,
            format=price_format,
            key=f"sl_slider_{column_index}",
            on_change=lambda idx=column_index: sync_sl_manual(idx)
        )
    
    with col_sl_manual:
        st.text("Manual")
        precio_stop_manual = st.number_input(
            "SL Manual",
            min_value=float(sl_min),
            max_value=float(sl_max),
            value=st.session_state[f"sl_manual_{column_index}"],
            step=step_size,
            format=price_format,
            key=f"sl_manual_{column_index}",
            on_change=lambda idx=column_index: sync_sl_slider(idx),
            label_visibility="collapsed"
        )
    
    # Aseguramos que precio_stop tenga el valor correcto (sea del slider o manual)
    precio_stop = st.session_state[f"sl_manual_{column_index}"]
    
    st.subheader("🎯 Take Profit")
    col_tp_slider, col_tp_manual = st.columns([3, 1])
    
    with col_tp_slider:
        precio_tp = st.slider(
            "Precio TP", 
            min_value=float(tp_min), 
            max_value=float(tp_max), 
            value=st.session_state[f"tp_slider_{column_index}"],
            step=step_size,
            format=price_format,
            key=f"tp_slider_{column_index}",
            on_change=lambda idx=column_index: sync_tp_manual(idx)
        )
    
    with col_tp_manual:
        st.text("Manual")
        precio_tp_manual = st.number_input(
            "TP Manual",
            min_value=float(tp_min),
            max_value=float(tp_max),
            value=st.session_state[f"tp_manual_{column_index}"],
            step=step_size,
            format=price_format,
            key=f"tp_manual_{column_index}",
            on_change=lambda idx=column_index: sync_tp_slider(idx),
            label_visibility="collapsed"
        )
    
    # Aseguramos que precio_tp tenga el valor correcto (sea del slider o manual)
    precio_tp = st.session_state[f"tp_manual_{column_index}"]

    # Riesgo máximo
    riesgo_max_usd = st.number_input("Riesgo máximo por operación ($)", min_value=0.01, value=20.0, key=f"riesgo_{column_index}")

    # --- Cálculos iniciales ---
    riesgo_por_accion_inicial = abs(precio_usuario - precio_stop)
    cantidad_acciones_inicial = int(riesgo_max_usd / riesgo_por_accion_inicial) if riesgo_por_accion_inicial > 0 else 0

    # --- Resultados de la Calculadora ---
    st.subheader("📊 Resultados")
    st.write(f"📌 Precio de entrada usado: **${precio_usuario:{price_format[1:]}}**")
    st.write(f"🛑 Precio de Stop Loss: **${precio_stop:{price_format[1:]}}**")
    st.write(f"🎯 Precio de Take Profit: **${precio_tp:{price_format[1:]}}**")
    st.write(f"🛑 Riesgo por acción: **${riesgo_por_accion_inicial:{price_format[1:]}}**")
    st.write(f"🔢 Cantidad máxima de acciones (con todo el riesgo en 1 entrada): **{cantidad_acciones_inicial}**")

    # --- Construcción de Posición (Gráfico de Promedio) ---
    with st.expander("⚙️ Gestión de Entradas"):
        num_entradas_promedio = st.slider("Número de Entradas Deseadas", min_value=1, max_value=5, value=1, step=1, key=f"num_entradas_gestion_{column_index}")
        if num_entradas_promedio > 0 and riesgo_por_accion_inicial > 0:
            acciones_por_entrada = int(cantidad_acciones_inicial / num_entradas_promedio)
            st.info(f"Si divides tu trade en **{num_entradas_promedio}** entradas, considera usar aproximadamente **{acciones_por_entrada}** acciones por entrada (ajusta según tu estrategia).")

        porcentaje_movimiento_promedio = st.number_input("Porcentaje de Movimiento entre Niveles (%)", min_value=0.1, max_value=20.0, value=2.0, step=0.1, key=f"porcentaje_mov_{column_index}") / 100

        data_promedio = [{"Nivel": 0, "Precio": precio_usuario, "Cantidad": 0, "Promedio": precio_usuario}]
        precio_actual_promedio = precio_usuario
        total_acciones_promedio = 0

        for i in range(num_entradas_promedio -1): # -1 because the first entry is at precio_usuario
            if tipo_operacion == "Long (Comprar)":
                precio_actual_promedio *= (1 - porcentaje_movimiento_promedio)
            elif tipo_operacion == "Short (Vender)":
                precio_actual_promedio *= (1 + porcentaje_movimiento_promedio)

            cantidad_acciones_nivel_promedio = st.number_input(f"Cantidad de Acciones Nivel {i+1}", min_value=1, value=acciones_por_entrada if num_entradas_promedio > 1 and cantidad_acciones_inicial > 0 else 1, step=1, key=f"cantidad_nivel_{column_index}_{i}")
            total_acciones_promedio += cantidad_acciones_nivel_promedio
            data_promedio.append({"Nivel": i + 1, "Precio": precio_actual_promedio, "Cantidad": total_acciones_promedio, "Promedio": 0}) # Placeholder for average

        # Calculate average prices
        for i, entry in enumerate(data_promedio):
            precio_ponderado_acumulado = 0
            total_cantidad_acumulada = 0
            for j in range(i + 1):
                precio_ponderado_acumulado += data_promedio[j]['Precio'] * (data_promedio[j]['Cantidad'] - (data_promedio[j-1]['Cantidad'] if j > 0 else 0))
                total_cantidad_acumulada += (data_promedio[j]['Cantidad'] - (data_promedio[j-1]['Cantidad'] if j > 0 else 0))
            data_promedio[i]['Promedio'] = precio_ponderado_acumulado / total_cantidad_acumulada if total_cantidad_acumulada > 0 else precio_usuario


        if len(data_promedio) > 1:
            df_promedio = pd.DataFrame(data_promedio)
            chart_promedio = alt.Chart(df_promedio).mark_line(point=True).encode(
                x=alt.X('Nivel:O', title='Nivel de Entrada (0 = Inicial)'),
                y=alt.Y('Promedio:Q', title='Precio Promedio de Entrada'),
                tooltip=['Nivel', alt.Tooltip('Precio', format=price_format), alt.Tooltip('Promedio', format=price_format), 'Cantidad']
            ).properties(
                title='Evolución del Precio Promedio al Construir Posición'
            )
            st.altair_chart(chart_promedio, use_container_width=True)

# --- Main App Layout for Three Tickers ---
col1, col2, col3 = st.columns(3)

with col1:
    analyze_ticker("AAPL", 1)

with col2:
    analyze_ticker("GOOG", 2)

with col3:
    analyze_ticker("TSLA", 3)
