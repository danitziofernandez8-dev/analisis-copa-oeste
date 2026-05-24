# ==========================================
# IMPORTACIONES
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_plotly_events import plotly_events

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Copa Oeste - Análisis", layout="wide")
st.title("🚌 Análisis de Rutas - Copa Oeste")

CAPACIDAD_BUS = 22

# ==========================================
# GRÁFICO INTERACTIVO
# ==========================================
def grafico_interactivo(datos, titulo, etiquetas_personalizadas=None, color="#7DB7E8"):

    if datos.empty:
        st.warning(f"⚠️ No hay datos en: {titulo}")
        return None

    df_chart = pd.DataFrame({
        "Ruta": datos.index.astype(str),
        "Valor": datos.values
    })

    df_chart["Valor"] = pd.to_numeric(df_chart["Valor"], errors="coerce").fillna(0)

    if etiquetas_personalizadas is not None:
        etiquetas = pd.to_numeric(etiquetas_personalizadas, errors="coerce").fillna(0)
        df_chart["Etiqueta"] = etiquetas.round(0).astype(int).astype(str)
    else:
        df_chart["Etiqueta"] = df_chart["Valor"].round(0).astype(int).astype(str)

    df_chart = df_chart.sort_values("Valor", ascending=False)

    fig = px.bar(df_chart, x="Ruta", y="Valor", text="Etiqueta", title=titulo)

    fig.update_traces(
        marker_color=color,
        textposition="outside",
        textfont_color="white",
        hovertemplate="<b>Ruta:</b> %{x}<br><b>Valor:</b> %{y}<extra></extra>"
    )

    fig.update_layout(
        plot_bgcolor="#08142c",
        paper_bgcolor="#08142c",
        font_color="white",
        height=550
    )

    sel = plotly_events(fig, click_event=True, key=titulo)

    return sel[0]["x"] if sel else None


# ==========================================
# UPLOAD
# ==========================================
archivo = st.file_uploader("📂 Sube Excel", type=["xlsx"])

if archivo:

    try:

        # ==========================================
        # CONFIG
        # ==========================================
        st.sidebar.header("⚙️ Configuración")

        tipo_movimiento = st.sidebar.radio("Movimiento", ["ENTRADA", "SALIDA"])
        tipo_analisis = st.sidebar.radio("Análisis", ["👥 Población", "⏱️ Tiempos"])

        # ==========================================
        # EXCEL
        # ==========================================
        excel = pd.ExcelFile(archivo)

        hoja = None
        for h in excel.sheet_names:
            if h.strip().upper() == tipo_movimiento:
                hoja = h
                break

        if hoja is None:
            st.error("❌ No existe hoja")
            st.stop()

        df_raw = pd.read_excel(archivo, sheet_name=hoja, header=None)

        # ==========================================
        # ENCABEZADO
        # ==========================================
        fila_enc = None
        for i, row in df_raw.iterrows():
            vals = [str(x).upper() for x in row.values]
            if any(k in vals for k in ["FECHA","RUTA","UNIDAD"]):
                fila_enc = i
                break

        columnas = df_raw.iloc[fila_enc].values

        cols = []
        contador = {}

        for i, c in enumerate(columnas):

            c = str(c).strip().upper()

            if c in ["", "NAN", "NONE", "UNNAMED"]:
                name = f"VACIO_{i}"
            else:
                contador[c] = contador.get(c, 0) + 1
                name = c if contador[c] == 1 else f"{c}_{contador[c]}"

            cols.append(name)

        df = df_raw.iloc[fila_enc+1:].copy()
        df.columns = cols
        df = df.dropna(how="all")

        df["RUTA"] = df["RUTA"].astype(str).str.upper().str.strip()

        visibles = [c for c in df.columns if not c.startswith("VACIO_")]

        # ==========================================
        # FECHA
        # ==========================================
        if "FECHA" in df.columns:
            df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

        # ==========================================
        # FILTRO MES
        # ==========================================
        if "FECHA" in df.columns:

            meses = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                     7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}

            df["PERIODO"] = df["FECHA"].dt.year.astype(str) + "-" + df["FECHA"].dt.month.map(meses)

            mes = st.sidebar.selectbox("Mes", ["Todos"] + sorted(df["PERIODO"].dropna().unique()))

            if mes != "Todos":
                df = df[df["PERIODO"] == mes]

        st.success("Archivo listo")
        st.dataframe(df[visibles].head())

        # ==========================================
        # POBLACIÓN
        # ==========================================
        if tipo_analisis == "👥 Población":

            st.header("👥 Análisis de Población")

            cols_aire = [c for c in visibles if "AIRE" in c]
            cols_tierra = [c for c in visibles if "TIERRA" in c]

            d = df.copy()

            for c in cols_aire + cols_tierra:
                d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)

            # ==========================================
            # TOTALES
            # ==========================================
            d["Aire"] = d[cols_aire].sum(axis=1)
            d["Tierra"] = d[cols_tierra].sum(axis=1)

            # ⭐ GENERAL NUEVO
            d["General"] = d["Aire"] + d["Tierra"]

            col_hora = next((c for c in ["H. PARTIDA","HORA SALIDA","HORA LLEGADA"] if c in d.columns), None)

            if not col_hora:
                st.error("Sin hora")
                st.stop()

            df_d = d.groupby(["FECHA","RUTA",col_hora]).agg(
                Aire=("Aire","sum"),
                Tierra=("Tierra","sum"),
                General=("General","sum"),
                Buses=("UNIDAD","nunique")
            ).reset_index()

            df_d["Capacidad"] = df_d["Buses"] * CAPACIDAD_BUS

            df_d["Load_Factor"] = df_d["General"] / df_d["Capacidad"] * 100

            df_d["Req_Buses"] = np.ceil(df_d["General"] / CAPACIDAD_BUS)

            df_d["Saturado"] = df_d["General"] > df_d["Capacidad"]

            # ==========================================
            # AGRUPACIÓN POR RUTA (SIN SESGO)
            # ==========================================
            ruta = df_d.groupby("RUTA").agg(
                Total_Aire=("Aire","sum"),
                Total_Tierra=("Tierra","sum"),
                Total_General=("General","sum"),
                Eventos=("General","count"),
                Max_Buses=("Buses","max"),
                Saturaciones=("Saturado","sum")
            )

            ruta["Promedio_Aire"] = ruta["Total_Aire"] / ruta["Eventos"]
            ruta["Promedio_Tierra"] = ruta["Total_Tierra"] / ruta["Eventos"]
            ruta["Promedio_General"] = ruta["Total_General"] / ruta["Eventos"]

            ruta["Load_Factor"] = ruta["Total_General"] / (ruta["Eventos"] * CAPACIDAD_BUS) * 100

            # ==========================================
            # SELECCIÓN GRÁFICA
            # ==========================================
            st.subheader("📊 Aire")
            grafico_interactivo(ruta["Promedio_Aire"], "Aire", color="#63B3ED")

            st.subheader("📊 Tierra")
            grafico_interactivo(ruta["Promedio_Tierra"], "Tierra", color="#68D391")

            st.subheader("📊 General")
            grafico_interactivo(ruta["Promedio_General"], "General", color="#F6AD55")

            # ==========================================
            # KPIs (USAN GENERAL)
            # ==========================================
            st.markdown("---")
            c1,c2,c3,c4 = st.columns(4)

            c1.metric("Promedio General", round(df_d["General"].mean(),1))
            c2.metric("Load Factor", f"{round(ruta['Load_Factor'].mean(),1)}%")
            c3.metric("Max Buses", int(ruta["Max_Buses"].max()))
            c4.metric("Saturaciones", int(ruta["Saturaciones"].sum()))

            st.dataframe(ruta.reset_index())

        # ==========================================
        # TIEMPOS
        # ==========================================
        if tipo_analisis == "⏱️ Tiempos":

            st.header("⏱️ Tiempos")

            p = next((c for c in ["H. PARTIDA","HORA SALIDA"] if c in df.columns), None)
            r = next((c for c in ["H. T1","H. T2","CONECTOR"] if c in df.columns), None)

            if p and r:

                dt = df.copy()
                dt["P"] = pd.to_datetime(dt[p], errors="coerce")
                dt["R"] = pd.to_datetime(dt[r], errors="coerce")

                dt = dt.dropna(subset=["P","R"])

                dt["Delay"] = (dt["R"] - dt["P"]).dt.total_seconds()/60

                tarde = dt.groupby("RUTA")["Delay"].apply(lambda x: (x>0).sum())

                grafico_interactivo(tarde, "Veces tarde", color="#FC8181")

                st.dataframe(tarde.reset_index())

            else:
                st.error("Sin columnas de tiempo")

    except Exception as e:
        st.error(f"Error: {e}")
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
