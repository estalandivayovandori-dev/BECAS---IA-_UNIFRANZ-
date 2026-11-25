import streamlit as st
import pandas as pd
import numpy as np
from difflib import SequenceMatcher

st.set_page_config(page_title="BECAS IA | Prototipo", page_icon="🎓", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
div[data-testid="stMetric"] {background:#f3f6fa; padding:14px; border-radius:12px;}
.small-note {color:#64748b; font-size:0.85rem;}
</style>
""", unsafe_allow_html=True)

st.title("🎓 BECAS IA")
st.subheader("Sistema de apoyo a la evaluación, alertas y supervisión humana")
st.info("PROTOTIPO ACADÉMICO · Datos completamente ficticios · La IA no adjudica ni rechaza becas.")

@st.cache_data
def crear_datos():
    rng = np.random.default_rng(2026)
    nombres = ["Natalia Rojas", "María Fernanda López", "Diego Vargas", "Lucía Méndez",
               "Andrés Flores", "Camila Salazar", "Jorge Pérez", "Valeria Quiroga",
               "Mateo Fernández", "Sofía Álvarez", "Daniela Cruz", "Pablo Ríos"]
    zonas = ["Centro", "Norte", "Sur", "Periférica A", "Periférica B", "Periférica C"]
    filas = []
    for i in range(1, 121):
        nombre = nombres[(i-1) % len(nombres)] + (f" {i}" if i > len(nombres) else "")
        zona = zonas[(i-1) % len(zonas)]
        filas.append({
            "ID": f"P-{i:03d}",
            "Postulante": nombre,
            "Calificación": int(rng.integers(55, 101)),
            "Ingreso familiar (Bs)": int(rng.integers(900, 6501)),
            "Integrantes del hogar": int(rng.integers(1, 8)),
            "Zona": zona,
            "Documentación": "Completa" if rng.random() > 0.13 else "Pendiente",
            "Revisión": "Pendiente"
        })
    df = pd.DataFrame(filas)
    # Registro demostrativo de Natalia, basado en el caso hipotético.
    df.loc[df["ID"] == "P-001", ["Postulante", "Calificación", "Ingreso familiar (Bs)", "Integrantes del hogar", "Zona", "Documentación"]] = [
        "Natalia Rojas", 96, 1450, 5, "Periférica A", "Completa"
    ]
    # Marcar 3 zonas con una reducción histórica simulada para auditar el sesgo.
    return df

if "datos" not in st.session_state:
    st.session_state.datos = crear_datos()
if "revisiones" not in st.session_state:
    st.session_state.revisiones = {}

df = st.session_state.datos.copy()

def puntaje(fila):
    academico = fila["Calificación"] * 0.40
    ingreso = max(0, min(100, (7000 - fila["Ingreso familiar (Bs)"]) / 60))
    economico = ingreso * 0.35
    hogar = min(100, fila["Integrantes del hogar"] * 15)
    familiar = hogar * 0.15
    documentacion = 100 if fila["Documentación"] == "Completa" else 0
    continuidad = documentacion * 0.10
    return round(academico + economico + familiar + continuidad, 2)

df["Puntaje referencial"] = df.apply(puntaje, axis=1)

# Alertas demostrativas y explicables
def alertas(fila):
    a = []
    if fila["ID"] == "P-001":
        a.append("Posible coincidencia de identidad: nombre similar a un registro externo ficticio; apellidos no coinciden.")
    if fila["Zona"] in ["Periférica A", "Periférica B", "Periférica C"]:
        a.append("Revisar posible impacto desigual por zona. El domicilio no debe reducir puntaje sin justificación objetiva.")
    if fila["Documentación"] == "Pendiente":
        a.append("Documentación pendiente: solicitar verificación antes de concluir la evaluación.")
    return a

df["Alertas"] = df.apply(lambda r: " | ".join(alertas(r)) if alertas(r) else "Sin alertas automáticas", axis=1)
df["Estado de revisión"] = df["ID"].map(st.session_state.revisiones).fillna("Pendiente")

# Navegación
menu = st.sidebar.radio("NAVEGACIÓN", [
    "Resumen general", "Expedientes y alertas", "Revisión humana",
    "Auditoría de equidad", "Simulador de corrección", "Privacidad y metodología"
])
st.sidebar.caption("Versión demostrativa 1.0")
st.sidebar.caption("No usar con datos personales reales.")

if menu == "Resumen general":
    st.header("Panel de control")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Postulantes", "120")
    c2.metric("Becas disponibles", "25")
    c3.metric("Expedientes con alertas", int(df["Alertas"].str.contains("Revisar|Posible|pendiente", case=False).sum()))
    c4.metric("Revisiones humanas", int((df["Estado de revisión"] != "Pendiente").sum()))
    st.markdown("### ¿Qué hace este sistema?")
    st.write("Organiza expedientes, calcula un puntaje referencial con criterios visibles y genera alertas para que el comité investigue posibles errores o impactos desiguales.")
    st.warning("Una alerta no demuestra fraude, deuda, discriminación ni identidad. Solo indica que hace falta revisar.")
    st.markdown("### Distribución de puntajes referenciales")
    st.bar_chart(df.set_index("ID")["Puntaje referencial"].head(25))
    st.markdown("### Principios de funcionamiento")
    st.columns(3)[0].success("Transparencia\n\nCriterios visibles")
    st.columns(3)[1].info("Supervisión humana\n\nDecisión del comité")
    st.columns(3)[2].success("Privacidad\n\nDatos ficticios y acceso limitado")

elif menu == "Expedientes y alertas":
    st.header("Expedientes y alertas")
    filtro = st.selectbox("Filtrar expedientes", ["Todos", "Con alertas", "Sin alertas"])
    vista = df.copy()
    if filtro == "Con alertas":
        vista = vista[vista["Alertas"] != "Sin alertas automáticas"]
    elif filtro == "Sin alertas":
        vista = vista[vista["Alertas"] == "Sin alertas automáticas"]
    st.dataframe(vista[["ID", "Postulante", "Calificación", "Ingreso familiar (Bs)", "Zona", "Puntaje referencial", "Alertas"]], use_container_width=True, hide_index=True)
    elegido = st.selectbox("Consultar expediente", df["ID"].tolist(), index=0)
    r = df[df["ID"] == elegido].iloc[0]
    st.markdown(f"### {r['Postulante']} · {r['ID']}")
    a, b, c = st.columns(3)
    a.metric("Calificación", r["Calificación"])
    b.metric("Puntaje referencial", r["Puntaje referencial"])
    c.metric("Estado documental", r["Documentación"])
    st.write(f"**Zona declarada:** {r['Zona']}  |  **Ingreso familiar:** Bs {r['Ingreso familiar (Bs)']:,}  |  **Integrantes:** {r['Integrantes del hogar']}")
    if alertas(r):
        for x in alertas(r):
            st.warning(x)
    else:
        st.success("No se generaron alertas con las reglas demostrativas.")
    st.caption("Las alertas se generan con reglas visibles y no sustituyen la comprobación documental.")

elif menu == "Revisión humana":
    st.header("Bandeja del comité revisor")
    st.write("El comité debe comprobar cada alerta y dejar constancia de su actuación.")
    candidatos = df[df["Alertas"] != "Sin alertas automáticas"]
    elegido = st.selectbox("Expediente para revisar", candidatos["ID"].tolist())
    r = df[df["ID"] == elegido].iloc[0]
    st.markdown(f"**{r['Postulante']} — {r['ID']}**")
    st.write(r["Alertas"])
    estado_actual = st.session_state.revisiones.get(elegido, "Pendiente")
    nuevo = st.selectbox("Resultado de revisión", ["Pendiente", "Verificado sin error", "Corregir registro", "Solicitar documentación", "Escalar a revisión especializada"],
                         index=["Pendiente", "Verificado sin error", "Corregir registro", "Solicitar documentación", "Escalar a revisión especializada"].index(estado_actual))
    motivo = st.text_area("Justificación del revisor (no dejar en blanco al registrar)")
    if st.button("Guardar revisión"):
        if nuevo == "Pendiente" or not motivo.strip():
            st.error("Selecciona un resultado y escribe una justificación.")
        else:
            st.session_state.revisiones[elegido] = nuevo
            st.session_state[f"motivo_{elegido}"] = motivo.strip()
            st.success("Revisión registrada en esta sesión de demostración.")
    st.markdown("### Registro de revisiones")
    registros = []
    for pid, estado in st.session_state.revisiones.items():
        registros.append({"ID": pid, "Estado": estado, "Justificación": st.session_state.get(f"motivo_{pid}", "")})
    st.dataframe(pd.DataFrame(registros), use_container_width=True, hide_index=True)

elif menu == "Auditoría de equidad":
    st.header("Auditoría de equidad territorial")
    st.write("Se compara la distribución de puntajes por zona para detectar patrones que merecen investigación. Una diferencia estadística no prueba por sí sola discriminación.")
    resumen = df.groupby("Zona").agg(Postulantes=("ID", "count"), Puntaje_promedio=("Puntaje referencial", "mean")).reset_index()
    st.dataframe(resumen.round(2), use_container_width=True, hide_index=True)
    st.bar_chart(resumen.set_index("Zona")["Puntaje_promedio"])
    st.warning("En este prototipo, el domicilio no forma parte de la fórmula del puntaje. Si una institución desea utilizarlo, debe justificar su pertinencia, necesidad y proporcionalidad, y evaluar impactos.")
    st.markdown("### Preguntas de auditoría")
    st.write("- ¿Existe una razón objetiva y comprobable para usar la zona?")
    st.write("- ¿Se aplica el mismo criterio a todos los postulantes?")
    st.write("- ¿Hay alternativas menos invasivas para medir dificultades de continuidad?")
    st.write("- ¿Se documentó el impacto de cada variable?")

elif menu == "Simulador de corrección":
    st.header("Simulador: ¿qué cambia si se corrige un error?")
    st.write("Ejemplo académico: comparar un expediente antes y después de retirar una coincidencia de identidad no verificada.")
    n = df[df["ID"] == "P-001"].iloc[0]
    st.metric("Puntaje referencial de Natalia", f"{n['Puntaje referencial']:.2f}/100")
    st.success("La coincidencia aproximada de identidad no se usa como penalización en esta fórmula. Por tanto, corregirla elimina una alerta, pero no altera el puntaje calculado.")
    st.markdown("### Orden referencial")
    ranking = df.sort_values("Puntaje referencial", ascending=False).reset_index(drop=True)
    ranking["Posición"] = np.arange(1, len(ranking)+1)
    ranking["Resultado ilustrativo"] = np.where(ranking["Posición"] <= 25, "Dentro de las primeras 25 posiciones", "Fuera de las primeras 25 posiciones")
    st.dataframe(ranking[["Posición", "ID", "Postulante", "Puntaje referencial", "Resultado ilustrativo"]].head(30), use_container_width=True, hide_index=True)
    st.caption("El orden no constituye adjudicación. Antes de decidir deben revisarse requisitos, empates, documentación, criterios publicados y garantías de impugnación.")

else:
    st.header("Privacidad, seguridad y metodología")
    st.subheader("Protección de datos")
    st.write("- Utilizar únicamente datos ficticios en esta demostración.")
    st.write("- Limitar el acceso a expedientes según funciones.")
    st.write("- No publicar nombres, domicilios, ingresos ni referencias de salud.")
    st.write("- Registrar quién consulta o modifica información en una versión de producción.")
    st.write("- Definir finalidad, conservación y eliminación de datos.")
    st.subheader("Metodología de puntaje ilustrativo")
    st.write("- Rendimiento académico: 40%.")
    st.write("- Situación económica: 35%.")
    st.write("- Composición del hogar: 15%.")
    st.write("- Documentación y continuidad: 10%.")
    st.warning("Estos pesos son exclusivamente didácticos. No son criterios oficiales ni una recomendación jurídica para adjudicar becas.")
    st.subheader("Límites")
    st.write("El prototipo no consulta registros externos, no verifica identidades reales, no realiza decisiones automatizadas y no sustituye asesoramiento jurídico ni evaluación institucional.")

st.divider()
st.caption("BECAS IA · Prototipo académico para análisis del Caso 4 · Cochabamba, Bolivia")
