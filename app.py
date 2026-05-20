import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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
# FUNCIÓN GRÁFICOS
# ==========================================
def grafico_barras(datos, titulo, sufijo=""):

    if datos.empty:
        st.warning(f"⚠️ No hay datos para mostrar en: {titulo}")
        return

    colores = [
        "#C9A227",
        "#5B8CC0",
        "#E0C76A",
        "#7FA7D8",
        "#D8C27A",
        "#2F5D9A",
        "#F2E3A3",
        "#4F81BD"
    ]

    colores_final = (
        colores * ((len(datos) // len(colores)) + 1)
    )[:len(datos)]

    fig, ax = plt.subplots(figsize=(10, 5))

    barras = ax.bar(
        datos.index.astype(str),
        datos.values,
        color=colores_final,
        edgecolor="white",
        linewidth=2
    )

    # ==========================================
    # FONDO OSCURO
    # ==========================================
    fig.patch.set_facecolor("#0b132b")
    ax.set_facecolor("#0b132b")

    # ==========================================
    # ESTILO
    # ==========================================
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.spines["bottom"].set_color("white")

    ax.grid(False)

    ax.set_title(
        titulo,
        fontsize=16,
        fontweight="bold",
        color="white",
        pad=20
    )

    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_yticks([])

    ax.tick_params(
        axis="x",
        labelsize=10,
        colors="white"
    )

    valor_maximo = max(datos.values)

    # ==========================================
    # ETIQUETAS
    # ==========================================
    for barra in barras:

        altura = barra.get_height()

        ax.text(
            barra.get_x() + barra.get_width() / 2,
            altura + (valor_maximo * 0.02),
            f"{int(altura)}{sufijo}",
            ha="center",
            fontsize=11,
            fontweight="bold",
            color="white"
        )

    ax.set_ylim(0, valor_maximo * 1.15)

    st.pyplot(fig)

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
            "HORA LLEGADA",
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

        for i, col in enumerate(columnas_reales):

            col_str = str(col).strip()

            if (
                pd.isna(col)
                or col_str == ""
                or col_str.lower() in ["nan", "none"]
                or col_str.startswith("Unnamed")
            ):

                columnas_limpias.append(f"VACIO_{i}")

            else:

                columnas_limpias.append(col_str)

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
        # SUBMENÚ POBLACIÓN
        # ==========================================
        submenu_poblacion = None

        if tipo_analisis == "👥 Población":

            submenu_poblacion = st.sidebar.radio(
                "👥 Tipo de Población",
                [
                    "✈️ Aire",
                    "🌎 Tierra"
                ]
            )

        # ==========================================
        # VISTA PREVIA
        # ==========================================
        st.success(
            f"✅ Archivo procesado correctamente - Hoja {tipo_movimiento}"
        )

        st.dataframe(
            df[columnas_visibles].head()
        )

        # ==========================================
        # POBLACIÓN
        # ==========================================
        if tipo_analisis == "👥 Población":

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
            # HORA
            # ==========================================
            col_hora = (
                "H. PARTIDA"
                if "H. PARTIDA" in df_pasajeros.columns
                else "HORA LLEGADA"
            )

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

            promedio_ruta = df_despachos.groupby(
                "RUTA"
            )[[
                "Total_Aire",
                "Total_Tierra"
            ]].mean()

            promedio_ruta = (
                promedio_ruta
                .round(0)
                .astype(int)
            )

            # ==========================================
            # AIRE
            # ==========================================
            if submenu_poblacion == "✈️ Aire":

                st.header(
                    f"✈️ Población Aire - {tipo_movimiento}"
                )

                grafico_barras(
                    promedio_ruta["Total_Aire"],
                    "✈️ Promedio Pasajeros Aire"
                )

                tabla_aire = promedio_ruta[
                    ["Total_Aire"]
                ].copy()

                tabla_aire.columns = [
                    "Promedio Aire"
                ]

                st.dataframe(
                    tabla_aire,
                    use_container_width=True
                )

            # ==========================================
            # TIERRA
            # ==========================================
            elif submenu_poblacion == "🌎 Tierra":

                st.header(
                    f"🌎 Población Tierra - {tipo_movimiento}"
                )

                grafico_barras(
                    promedio_ruta["Total_Tierra"],
                    "🌎 Promedio Pasajeros Tierra"
                )

                tabla_tierra = promedio_ruta[
                    ["Total_Tierra"]
                ].copy()

                tabla_tierra.columns = [
                    "Promedio Tierra"
                ]

                st.dataframe(
                    tabla_tierra,
                    use_container_width=True
                )

            # ==========================================
            # LOAD FACTOR
            # ==========================================
            st.markdown("---")

            st.header("🚌 Load Factor")

            df_despachos["Capacidad_Total"] = (
                df_despachos["Buses_Despachados"]
                * CAPACIDAD_BUS
            )

            df_despachos["Load_Factor"] = (
                (
                    df_despachos["Total_Pasajeros"]
                    / df_despachos["Capacidad_Total"]
                ) * 100
            )

            df_despachos["Load_Factor"] = (
                df_despachos["Load_Factor"]
                .round(0)
                .astype(int)
            )

            load_factor_ruta = df_despachos.groupby(
                "RUTA"
            )["Load_Factor"].mean()

            load_factor_ruta = (
                load_factor_ruta
                .round(0)
                .astype(int)
            )

            grafico_barras(
                load_factor_ruta,
                "🚌 Promedio General Load Factor",
                "%"
            )

            tabla_load = (
                load_factor_ruta.reset_index()
            )

            tabla_load.columns = [
                "Ruta",
                "Load Factor"
            ]

            tabla_load["Load Factor"] = (
                tabla_load["Load Factor"]
                .astype(str) + "%"
            )

            st.dataframe(
                tabla_load,
                use_container_width=True
            )

        # ==========================================
        # TIEMPOS
        # ==========================================
        if tipo_analisis == "⏱️ Tiempos":

            st.header(
                f"⏱️ Análisis de Tiempos - {tipo_movimiento}"
            )

            if (
                "HORA LLEGADA" in df.columns
                and "CONECTOR" in df.columns
            ):

                df_tiempos = df.copy()

                df_tiempos["Hora_Programada"] = pd.to_datetime(
                    df_tiempos["HORA LLEGADA"],
                    errors="coerce"
                )

                df_tiempos["Hora_Real"] = pd.to_datetime(
                    df_tiempos["CONECTOR"],
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

                # ==========================================
                # VECES TARDE
                # ==========================================
                st.markdown("---")

                veces_tarde = df_tiempos.groupby(
                    "RUTA"
                )["Llego_Tarde"].sum()

                veces_tarde = (
                    veces_tarde
                    .round(0)
                    .astype(int)
                )

                grafico_barras(
                    veces_tarde,
                    "🚨 Cantidad de Veces Tarde"
                )

                st.dataframe(
                    veces_tarde.reset_index(),
                    use_container_width=True
                )

            else:

                st.error(
                    "❌ No existen columnas HORA LLEGADA o CONECTOR"
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