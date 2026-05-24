import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_plotly_events import plotly_events

# ==========================================
# CONFIGURACIÓN PÁGINA
# ==========================================
st.set_page_config(
    page_title="Copa Oeste - Análisis",
    layout="wide"
)

st.title("🚌 Análisis de Rutas - Copa Oeste")

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================
CAPACIDAD_BUS = 22

# ==========================================
# FUNCIÓN GRÁFICO
# ==========================================
def grafico_interactivo(
    datos,
    titulo,
    etiquetas_personalizadas=None
):

    if datos.empty:

        st.warning(
            f"⚠️ No hay datos para mostrar en: {titulo}"
        )

        return

    # ==========================================
    # DATAFRAME
    # ==========================================
    df_chart = pd.DataFrame({
        "Ruta": datos.index.astype(str),
        "Valor": datos.values
    })

    # ==========================================
    # ETIQUETAS
    # ==========================================
    if etiquetas_personalizadas is not None:

        df_chart["Etiqueta"] = (
            etiquetas_personalizadas
            .astype(str)
        )

    else:

        df_chart["Etiqueta"] = (
            datos.astype(str)
        )

    # ==========================================
    # GRÁFICA
    # ==========================================
    fig = px.bar(
        df_chart,
        x="Ruta",
        y="Valor",
        text="Etiqueta",
        title=titulo
    )

    # ==========================================
    # ESTILO
    # ==========================================
    fig.update_layout(
        plot_bgcolor="#0b132b",
        paper_bgcolor="#0b132b",
        font_color="white",
        title_font_size=20,
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
        height=500
    )

    # ==========================================
    # TEXTO
    # ==========================================
    fig.update_traces(
        textposition="outside"
    )

    # ==========================================
    # MOSTRAR
    # ==========================================
    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==========================================
# SUBIR ARCHIVO
# ==========================================
archivo = st.file_uploader(
    "📂 Sube el Excel de Rutas",
    type=["xlsx"]
)

if archivo:

    try:

        # ==========================================
        # SIDEBAR
        # ==========================================
        st.sidebar.header("⚙️ Configuración")

        tipo_movimiento = st.sidebar.radio(
            "🚌 Tipo de Movimiento",
            [
                "ENTRADA",
                "SALIDA"
            ]
        )

        tipo_analisis = st.sidebar.radio(
            "📌 Tipo de Análisis",
            [
                "👥 Población",
                "⏱️ Tiempos"
            ]
        )

        # ==========================================
        # LEER EXCEL
        # ==========================================
        excel_file = pd.ExcelFile(archivo)

        hoja_real = None

        for hoja in excel_file.sheet_names:

            if hoja.strip().upper() == tipo_movimiento:

                hoja_real = hoja
                break

        if hoja_real is None:

            st.error(
                f"❌ No existe la pestaña {tipo_movimiento}"
            )

            st.stop()

        # ==========================================
        # LEER RAW
        # ==========================================
        df_raw = pd.read_excel(
            archivo,
            sheet_name=hoja_real,
            header=None
        )

        # ==========================================
        # BUSCAR ENCABEZADO
        # ==========================================
        fila_encabezado = None

        palabras_clave = [
            "FECHA",
            "RUTA",
            "UNIDAD"
        ]

        for idx, row in df_raw.iterrows():

            valores = [
                str(v).strip().upper()
                for v in row.values
            ]

            if any(pc in valores for pc in palabras_clave):

                fila_encabezado = idx
                break

        if fila_encabezado is None:

            st.error("❌ No se detectó encabezado")
            st.stop()

        # ==========================================
        # LIMPIAR COLUMNAS
        # ==========================================
        columnas_reales = (
            df_raw.iloc[fila_encabezado].values
        )

        columnas_limpias = []
        contador_columnas = {}

        for i, col in enumerate(columnas_reales):

            col_str = str(col).strip()

            if (
                pd.isna(col)
                or col_str == ""
                or col_str.lower() in ["nan", "none"]
                or col_str.startswith("Unnamed")
            ):

                nombre_final = f"VACIO_{i}"

            else:

                nombre_base = col_str

                if nombre_base in contador_columnas:

                    contador_columnas[nombre_base] += 1

                    nombre_final = (
                        f"{nombre_base}_{contador_columnas[nombre_base]}"
                    )

                else:

                    contador_columnas[nombre_base] = 1
                    nombre_final = nombre_base

            columnas_limpias.append(nombre_final)

        # ==========================================
        # DATAFRAME
        # ==========================================
        df = df_raw.iloc[
            fila_encabezado + 1:
        ].copy()

        df.columns = columnas_limpias

        df = (
            df.dropna(how="all")
            .reset_index(drop=True)
        )

        columnas_visibles = [
            c for c in df.columns
            if not str(c).startswith("VACIO_")
        ]

        # ==========================================
        # FECHA
        # ==========================================
        if "FECHA" in df.columns:

            df["FECHA_PROCESADA"] = pd.to_datetime(
                df["FECHA"],
                errors="coerce"
            )

        # ==========================================
        # FILTRO MES
        # ==========================================
        st.sidebar.header("📅 Filtros")

        if (
            "FECHA_PROCESADA" in df.columns
            and not df["FECHA_PROCESADA"].dropna().empty
        ):

            meses_es = {
                1: "Enero",
                2: "Febrero",
                3: "Marzo",
                4: "Abril",
                5: "Mayo",
                6: "Junio",
                7: "Julio",
                8: "Agosto",
                9: "Septiembre",
                10: "Octubre",
                11: "Noviembre",
                12: "Diciembre"
            }

            df["PERIODO"] = (
                df["FECHA_PROCESADA"]
                .dt.year.astype(str)
                + " - "
                + df["FECHA_PROCESADA"]
                .dt.month.map(meses_es)
            )

            lista_periodos = sorted(
                df["PERIODO"].dropna().unique()
            )

            periodo = st.sidebar.selectbox(
                "Selecciona Mes:",
                ["Todos"] + lista_periodos
            )

            if periodo != "Todos":

                df = df[
                    df["PERIODO"] == periodo
                ]

        # ==========================================
        # POBLACIÓN
        # ==========================================
        if tipo_analisis == "👥 Población":

            submenu_poblacion = st.sidebar.radio(
                "👥 Tipo de Población",
                [
                    "✈️ Aire",
                    "🌎 Tierra"
                ]
            )

            st.header(
                f"👥 Análisis de Población - {tipo_movimiento}"
            )

            cols_aire = [
                c for c in columnas_visibles
                if "AIRE" in c.upper()
            ]

            cols_tierra = [
                c for c in columnas_visibles
                if "TIERRA" in c.upper()
            ]

            df_pasajeros = df.copy()

            for col in cols_aire + cols_tierra:

                df_pasajeros[col] = pd.to_numeric(
                    df_pasajeros[col],
                    errors="coerce"
                ).fillna(0)

            # ==========================================
            # TOTALES
            # ==========================================
            df_pasajeros["Total_Aire"] = (
                df_pasajeros[cols_aire]
                .sum(axis=1)
            )

            df_pasajeros["Total_Tierra"] = (
                df_pasajeros[cols_tierra]
                .sum(axis=1)
            )

            df_pasajeros["Total_Pasajeros"] = (
                df_pasajeros["Total_Aire"]
                + df_pasajeros["Total_Tierra"]
            )

            # ==========================================
            # DETECTAR HORA
            # ==========================================
            posibles_horas = [
                "H. PARTIDA",
                "HORA LLEGADA",
                "HORA SALIDA"
            ]

            col_hora = None

            for col in posibles_horas:

                if col in df_pasajeros.columns:

                    col_hora = col
                    break

            if col_hora is None:

                st.error(
                    "❌ No se encontró columna de hora"
                )

                st.stop()

            # ==========================================
            # CONSOLIDAR
            # ==========================================
            df_despachos = df_pasajeros.groupby(
                ["FECHA", "RUTA", col_hora]
            ).agg(
                Total_Aire=("Total_Aire", "sum"),
                Total_Tierra=("Total_Tierra", "sum"),
                Total_Pasajeros=("Total_Pasajeros", "sum"),
                Buses_Despachados=("UNIDAD", "nunique")
            ).reset_index()

            # ==========================================
            # LOAD FACTOR REAL
            # ==========================================
            df_despachos["Load_Factor_Real"] = (
                (
                    df_despachos["Total_Pasajeros"]
                    / CAPACIDAD_BUS
                ) * 100
            )

            df_despachos["Load_Factor_Real"] = (
                df_despachos["Load_Factor_Real"]
                .round(0)
                .astype(int)
            )

            # ==========================================
            # BUSES REQUERIDOS
            # ==========================================
            df_despachos["Buses_Requeridos"] = (
                (
                    df_despachos["Total_Pasajeros"]
                    / CAPACIDAD_BUS
                )
            ).apply(np.ceil)

            df_despachos["Buses_Requeridos"] = (
                df_despachos["Buses_Requeridos"]
                .astype(int)
            )

            # ==========================================
            # SATURACIÓN
            # ==========================================
            df_despachos["Frecuencia_Saturada"] = (
                df_despachos["Total_Pasajeros"]
                > CAPACIDAD_BUS
            )

            # ==========================================
            # PROMEDIOS REALES
            # ==========================================
            promedio_ruta = df_despachos.groupby(
                "RUTA"
            ).agg(
                Promedio_Aire=("Total_Aire", "mean"),
                Promedio_Tierra=("Total_Tierra", "mean"),
                Promedio_Total=("Total_Pasajeros", "mean"),
                Maximo_Pasajeros=("Total_Pasajeros", "max"),
                Promedio_Load_Factor=("Load_Factor_Real", "mean"),
                Maximo_Load_Factor=("Load_Factor_Real", "max"),
                Veces_Saturada=("Frecuencia_Saturada", "sum"),
                Maximo_Buses_Usados=("Buses_Despachados", "max"),
                Promedio_Buses_Requeridos=("Buses_Requeridos", "mean")
            ).round(0)

            promedio_ruta = (
                promedio_ruta
                .astype(int)
            )

            # ==========================================
            # GRÁFICAS
            # ==========================================
            if submenu_poblacion == "✈️ Aire":

                grafico_interactivo(
                    promedio_ruta["Promedio_Aire"],
                    "✈️ Promedio Real Pasajeros Aire",
                    etiquetas_personalizadas=promedio_ruta["Promedio_Total"]
                )

            elif submenu_poblacion == "🌎 Tierra":

                grafico_interactivo(
                    promedio_ruta["Promedio_Tierra"],
                    "🌎 Promedio Real Pasajeros Tierra",
                    etiquetas_personalizadas=promedio_ruta["Promedio_Total"]
                )

            # ==========================================
            # KPIs
            # ==========================================
            st.markdown("---")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "👥 Promedio Total",
                int(
                    promedio_ruta["Promedio_Total"]
                    .mean()
                )
            )

            col2.metric(
                "🚨 Máxima Saturación",
                str(
                    int(
                        promedio_ruta[
                            "Maximo_Load_Factor"
                        ].max()
                    )
                ) + "%"
            )

            col3.metric(
                "🚌 Máx. Buses Utilizados",
                int(
                    promedio_ruta[
                        "Maximo_Buses_Usados"
                    ].max()
                )
            )

            col4.metric(
                "⚠️ Veces Saturada",
                int(
                    promedio_ruta[
                        "Veces_Saturada"
                    ].sum()
                )
            )

            # ==========================================
            # LOAD FACTOR
            # ==========================================
            st.markdown("---")

            st.header(
                "🚌 Saturación Real Promedio"
            )

            grafico_interactivo(
                promedio_ruta["Promedio_Load_Factor"],
                "🚌 Saturación Real"
            )

            # ==========================================
            # TABLA
            # ==========================================
            st.markdown("---")

            tabla_load = promedio_ruta.reset_index()

            st.dataframe(
                tabla_load,
                use_container_width=True
            )

            # ==========================================
            # DETALLE OPERATIVO
            # ==========================================
            st.markdown("---")

            st.subheader(
                "📋 Detalle Operativo"
            )

            detalle_operativo = df_despachos[[
                "FECHA",
                "RUTA",
                col_hora,
                "Total_Aire",
                "Total_Tierra",
                "Total_Pasajeros",
                "Load_Factor_Real",
                "Buses_Despachados",
                "Buses_Requeridos"
            ]].copy()

            detalle_operativo.columns = [
                "Fecha",
                "Ruta",
                "Hora",
                "Pasajeros Aire",
                "Pasajeros Tierra",
                "Pasajeros Totales",
                "Load Factor Real",
                "Buses Utilizados",
                "Buses Requeridos"
            ]

            detalle_operativo["Load Factor Real"] = (
                detalle_operativo["Load Factor Real"]
                .astype(str) + "%"
            )

            st.dataframe(
                detalle_operativo,
                use_container_width=True
            )

        # ==========================================
        # TIEMPOS
        # ==========================================
        if tipo_analisis == "⏱️ Tiempos":

            st.header(
                f"⏱️ Análisis de Tiempos - {tipo_movimiento}"
            )

            col_programada = None

            posibles_programadas = [
                "HORA LLEGADA",
                "HORA SALIDA",
                "H. PARTIDA"
            ]

            for col in posibles_programadas:

                if col in df.columns:

                    col_programada = col
                    break

            col_real = None

            posibles_reales = [
                "CONECTOR",
                "H. T1",
                "H. T2",
                "H. TC"
            ]

            for col in posibles_reales:

                if col in df.columns:

                    col_real = col
                    break

            if (
                col_programada is not None
                and col_real is not None
            ):

                df_tiempos = df.copy()

                df_tiempos["Hora_Programada"] = pd.to_datetime(
                    df_tiempos[col_programada],
                    errors="coerce"
                )

                df_tiempos["Hora_Real"] = pd.to_datetime(
                    df_tiempos[col_real],
                    errors="coerce"
                )

                df_tiempos = df_tiempos.dropna(
                    subset=[
                        "Hora_Programada",
                        "Hora_Real"
                    ]
                )

                df_tiempos["Diferencia_Min"] = (
                    df_tiempos["Hora_Real"]
                    - df_tiempos["Hora_Programada"]
                ).dt.total_seconds() / 60

                df_tiempos["Llego_Tarde"] = (
                    df_tiempos["Diferencia_Min"] > 0
                )

                veces_tarde = df_tiempos.groupby(
                    "RUTA"
                )["Llego_Tarde"].sum()

                veces_tarde = (
                    veces_tarde
                    .round(0)
                    .astype(int)
                )

                st.markdown("---")

                grafico_interactivo(
                    veces_tarde,
                    "🚨 Cantidad de Veces Tarde"
                )

                st.dataframe(
                    veces_tarde.reset_index(),
                    use_container_width=True
                )

            else:

                st.error(
                    "❌ No existen columnas válidas para análisis de tiempos"
                )

    except Exception as e:

        st.error(
            f"❌ Error general durante el procesamiento: {e}"
        )
        # =====================================================================
        # === BOTÓN DE DESCARGA DIRECTA (REEMPLAZA DROPBOX SEGURO EN LA WEB) ===
        # =====================================================================
        if df_reporte_jefa is not None:
            st.markdown("---")
            st.subheader("📋 Generación de Reporte Ejecutivo")

            # Estructura limpia y responsiva en formato HTML para descarga web
            html_contenido = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Reporte Análisis Copa Oeste</title>
                <meta name='viewport' content='width=device-width, initial-scale=1'>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body class="bg-light p-4">
                <div class="container bg-white p-4 rounded shadow-sm" style="border-left: 5px solid #003B7A; max-width: 800px; margin: 0 auto;">
                    <h2 class="text-primary mb-1" style="color: #003B7A !important; font-weight: bold;">📊 Reporte Operativo - Copa Oeste</h2>
                    <p class="text-muted small">Auditoría de rendimiento, ocupación y puntualidad de rutas</p>
                    <hr>
                    <h4 class="mb-3 text-secondary" style="font-size: 1.15rem;">{titulo_seccion_reporte}</h4>
                    <div class="table-responsive">
                        {df_reporte_jefa.to_html(classes='table table-striped table-hover table-bordered align-middle', index=False)}
                    </div>
                </div>
            </body>
            </html>
            """

            st.download_button(
                label="📥 Descargar Reporte HTML",
                data=html_contenido,
                file_name="Reporte_Analisis_Copa_Oeste.html",
                mime="text/html",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"❌ Error general durante el procesamiento: {e}")