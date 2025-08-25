import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import plotly.express as px

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Gestión de Licitaciones Kaiken",
    page_icon="🏢",
    layout="wide",
)

# --- FUNCIÓN DE VALIDACIÓN DE RUT CHILENO ---
def validar_rut(rut):
    """Valida un RUT chileno (formato XX.XXX.XXX-Y)."""
    try:
        rut = rut.upper().replace(".", "").replace("-", "")
        if not rut[:-1].isdigit() or len(rut) < 8:
            return False
        
        cuerpo = rut[:-1]
        dv_ingresado = rut[-1]
        
        suma = 0
        multiplo = 2
        for d in reversed(cuerpo):
            suma += int(d) * multiplo
            multiplo = multiplo + 1 if multiplo < 7 else 2
            
        dv_calculado = 11 - (suma % 11)
        
        if dv_calculado == 11:
            dv_esperado = '0'
        elif dv_calculado == 10:
            dv_esperado = 'K'
        else:
            dv_esperado = str(dv_calculado)
            
        return dv_ingresado == dv_esperado
    except:
        return False

# --- CONEXIÓN A LA BASE DE DATOS (CON GESTOR INTELIGENTE) ---
@st.cache_resource
def init_connection():
    """Inicializa y cachea la conexión a la base de datos."""
    return psycopg2.connect(**st.secrets["database"])

def get_connection():
    """
    Obtiene una conexión del cache y verifica si está activa.
    Si no lo está, limpia el cache y establece una nueva conexión.
    """
    try:
        conn = init_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1") # "Ping" para verificar la conexión
        cursor.close()
    except (psycopg2.InterfaceError, psycopg2.OperationalError):
        st.cache_resource.clear()
        conn = init_connection()
    return conn

conn = get_connection()

# --- FUNCIONES DE DATOS (QUERIES) ---
@st.cache_data(ttl=300) # Cache de 5 minutos
def load_data(query):
    """Ejecuta una consulta SQL y la cachea."""
    return pd.read_sql_query(query, conn)

# --- PÁGINAS DE LA APLICACIÓN (MODULARIZADAS) ---

def page_dashboard():
    st.title("📊 Dashboard de Inteligencia de Negocios")
    
    query = """
        SELECT 
            ovm.*, 
            c.nom_cli, 
            t.creation_date 
        FROM public.order_details_with_margin ovm
        JOIN public.tenders t ON ovm.tender_id = t.id
        JOIN public.clientes c ON t.id_cli = c.id_cli;
    """
    df = load_data(query)
    
    if df.empty:
        st.warning("No hay datos suficientes para mostrar en el dashboard.")
        return

    df['creation_date'] = pd.to_datetime(df['creation_date'])
    df['revenue'] = df['sale_price'] * df['quantity']

    st.header("Filtros Globales")
    date_range = st.date_input(
        "Selecciona un rango de fechas:",
        value=(df['creation_date'].min(), df['creation_date'].max()),
        min_value=df['creation_date'].min(),
        max_value=df['creation_date'].max()
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df['creation_date'] >= pd.to_datetime(start_date)) & (df['creation_date'] <= pd.to_datetime(end_date))]
    
    if df.empty:
        st.warning("No hay datos en el rango de fechas seleccionado.")
        return

    st.markdown("---")
    st.header("1. Análisis de Rentabilidad por Cliente")
    st.info("**Decisión a tomar:** ¿Qué clientes nos generan más ganancias (margen) en relación a lo que compran (ingresos)?")

    df_clients = df.groupby('nom_cli').agg(
        total_margin=('total_margin', 'sum'),
        revenue=('revenue', 'sum'),
        num_tenders=('tender_id', 'nunique')
    ).reset_index()
    
    df_clients['avg_margin_percentage'] = (df_clients['total_margin'] / df_clients['revenue']) * 100

    fig_bubble = px.scatter(
        df_clients, x="revenue", y="total_margin", size="num_tenders", color="nom_cli",
        hover_name="nom_cli",
        custom_data=['nom_cli', 'revenue', 'total_margin', 'num_tenders', 'avg_margin_percentage'],
        size_max=60, title="Ingresos vs. Margen por Cliente",
        labels={"revenue": "Ingresos Totales ($)", "total_margin": "Margen Total ($)", "nom_cli": "Cliente"},
        template="plotly_white"
    )
    fig_bubble.update_traces(
        marker=dict(line=dict(width=1, color='DarkSlateGrey')),
        hovertemplate="<br>".join([
            "<b>%{customdata[0]}</b>",
            "Ingresos: $%{customdata[1]:,.2f}",
            "Margen: $%{customdata[2]:,.2f}",
            "N° Licitaciones: %{customdata[3]}",
            "Margen Promedio: %{customdata[4]:.2f}%"
        ])
    )
    st.plotly_chart(fig_bubble, use_container_width=True)
    
    st.markdown("---")
    st.header("2. Top 5 Clientes y Productos (Análisis Pareto)")
    st.info("**Decisión a tomar:** ¿Dónde debemos enfocar nuestros esfuerzos comerciales (regla del 80/20)?")

    col1, col2 = st.columns(2)
    
    top_clients = df_clients.nlargest(5, 'total_margin')
    fig_top_clients = px.bar(top_clients, x='nom_cli', y='total_margin', title="Top 5 Clientes por Margen Generado", color='nom_cli', text_auto='$,.2f')
    col1.plotly_chart(fig_top_clients, use_container_width=True)

    df_products = df.groupby('product_name')['total_margin'].sum().reset_index()
    top_products = df_products.nlargest(5, 'total_margin')
    fig_top_products = px.bar(top_products, x='product_name', y='total_margin', title="Top 5 Productos por Margen Generado", color='product_name', text_auto='$,.2f')
    col2.plotly_chart(fig_top_products, use_container_width=True)

    st.markdown("---")
    st.header("3. Análisis de Tendencias")
    st.info("**Decisión a tomar:** ¿Nuestros ingresos están creciendo o disminuyendo? ¿Hay meses de temporada alta?")

    df_time = df.set_index('creation_date').resample('M').agg(
        monthly_revenue=('revenue', 'sum'),
        monthly_margin=('total_margin', 'sum')
    ).reset_index()

    fig_time = px.line(
        df_time, x='creation_date', y=['monthly_revenue', 'monthly_margin'],
        title="Evolución de Ingresos y Márgenes por Mes",
        labels={'creation_date': 'Mes', 'value': 'Monto ($)'}, markers=True
    )
    fig_time.update_traces(hovertemplate='Monto: $%{y:,.2f}<br>Mes: %{x|%Y-%m}')
    st.plotly_chart(fig_time, use_container_width=True)

def page_ver_licitaciones():
    st.title("📑 Búsqueda y Análisis de Licitaciones")
    
    query = """
        SELECT 
            t.id as "ID Licitación", c.nom_cli as "Cliente", c.rut_cli as "RUT Cliente",
            t.creation_date as "Fecha Creación", t.delivery_date as "Fecha Entrega",
            ovm.product_name as "Producto", ovm.quantity as "Cantidad",
            ovm.sale_price as "Precio Venta", ovm.cost_price as "Costo",
            ovm.total_margin as "Margen Producto"
        FROM public.tenders t
        JOIN public.clientes c ON t.id_cli = c.id_cli
        LEFT JOIN public.order_details_with_margin ovm ON t.id = ovm.tender_id
        ORDER BY t.creation_date DESC;
    """
    df_full = load_data(query)

    if df_full.empty:
        st.warning("No hay licitaciones registradas para mostrar.")
        return

    st.header("Herramienta de Búsqueda")
    lista_licitaciones = df_full.drop_duplicates(subset=["ID Licitación"]).set_index("ID Licitación")
    search_query = st.text_input("Buscar por ID de Licitación o Nombre de Cliente:", "")

    if search_query:
        mask = (lista_licitaciones.index.str.contains(search_query, case=False, na=False) | 
                lista_licitaciones["Cliente"].str.contains(search_query, case=False, na=False))
        opciones_filtradas = lista_licitaciones[mask].index
    else:
        opciones_filtradas = lista_licitaciones.index

    selected_tender_id = st.selectbox(
        "Selecciona una Licitación:", options=opciones_filtradas,
        format_func=lambda x: f"{x} - {lista_licitaciones.loc[x, 'Cliente']}"
    )

    if selected_tender_id:
        st.markdown("---")
        st.header(f"Análisis Completo de la Licitación: {selected_tender_id}")
        df_selected = df_full[df_full["ID Licitación"] == selected_tender_id]
        
        st.subheader("Datos Generales")
        info_general = df_selected.iloc[0]
        col1, col2, col3 = st.columns(3)
        col1.metric("Cliente", info_general["Cliente"])
        col2.metric("Fecha Creación", f"{info_general['Fecha Creación']:%Y-%m-%d}")
        col3.metric("Fecha Entrega", f"{info_general['Fecha Entrega']:%Y-%m-%d}")

        st.subheader("Métricas de Rentabilidad")
        total_revenue = (df_selected["Precio Venta"] * df_selected["Cantidad"]).sum()
        total_cost = (df_selected["Costo"] * df_selected["Cantidad"]).sum()
        total_margin = df_selected["Margen Producto"].sum()
        margin_percentage = (total_margin / total_revenue) * 100 if total_revenue > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ingresos Totales", f"${total_revenue:,.2f}")
        m2.metric("Costos Totales", f"${total_cost:,.2f}")
        m3.metric("Margen Total", f"${total_margin:,.2f}", delta=f"{margin_percentage:.2f}%")
        m4.metric("N° de Productos", f"{len(df_selected)}")
        
        st.subheader("Detalle de Productos Adjudicados")
        df_display = df_selected[["Producto", "Cantidad", "Precio Venta", "Costo", "Margen Producto"]]
        
        st.dataframe(
            df_display, use_container_width=True, hide_index=True,
            column_config={
                "Precio Venta": st.column_config.NumberColumn(format="$ %(,.2f"),
                "Costo": st.column_config.NumberColumn(format="$ %(,.2f"),
                "Margen Producto": st.column_config.NumberColumn(format="$ %(,.2f"),
            }
        )
        
def page_gestionar_licitacion():
    st.title("✍️ Gestionar Licitaciones")

    modo = st.selectbox("¿Qué deseas hacer?", ["Crear Nueva Licitación", "Editar Licitación Existente"], key="modo_licitacion")

    clients_df = load_data("SELECT id_cli, nom_cli FROM public.clientes ORDER BY nom_cli;")
    products_df = load_data("SELECT sku_pro, nom_pro, cost_prp FROM public.products ORDER BY nom_pro;")
    tenders_df = load_data("SELECT id, id_cli FROM public.tenders;")

    tender_id_default, client_id_default, selected_products_default = "", None, []
    creation_date_default = datetime.today()
    delivery_date_default = creation_date_default + timedelta(days=1)

    if modo == "Editar Licitación Existente":
        st.subheader("Selecciona la Licitación a Editar")
        tender_a_editar = st.selectbox("Buscar Licitación por ID:", options=tenders_df['id'], index=None, placeholder="Escribe o selecciona un ID...")
        if tender_a_editar:
            tender_id_default = tender_a_editar
            tender_data = load_data(f"SELECT * FROM public.tenders WHERE id = '{tender_a_editar}';").iloc[0]
            client_id_default, creation_date_default, delivery_date_default = tender_data['id_cli'], tender_data['creation_date'], tender_data['delivery_date']
            order_data = load_data(f"SELECT product_id, quantity, price FROM public.orders WHERE tender_id = '{tender_a_editar}';")
            skus_seleccionados = order_data['product_id'].tolist()
            selected_products_default = products_df[products_df['sku_pro'].isin(skus_seleccionados)]['nom_pro'].tolist()
            st.session_state['productos_a_editar'] = order_data.set_index('product_id').to_dict('index')

    st.markdown("---")
    st.subheader("Datos de la Licitación")

    creation_date = st.date_input("Fecha Creación", value=creation_date_default)
    min_delivery_date = creation_date + timedelta(days=1)
    delivery_date = st.date_input("Fecha Entrega", value=delivery_date_default, min_value=min_delivery_date)

    with st.form("gestion_licitacion_form"):
        client_names, client_index = clients_df['nom_cli'].tolist(), None
        if client_id_default:
            client_name_default = clients_df[clients_df['id_cli'] == client_id_default]['nom_cli'].iloc[0]
            if client_name_default in client_names:
                client_index = client_names.index(client_name_default)

        tender_id = st.text_input("ID Licitación", value=tender_id_default, disabled=(modo == "Editar Licitación Existente"))
        selected_client_name = st.selectbox("Cliente", options=client_names, index=client_index)
        
        st.markdown("---")
        st.subheader("Productos Adjudicados")
        selected_products = st.multiselect("Selecciona productos:", options=products_df['nom_pro'], default=selected_products_default)
        
        products_to_add = []
        if selected_products:
            for product_name in selected_products:
                product_row = products_df[products_df['nom_pro'] == product_name].iloc[0]
                sku, cost = product_row['sku_pro'], product_row['cost_prp']
                qty_default, price_default = 1, cost + 0.01
                if modo == "Editar Licitación Existente" and sku in st.session_state.get('productos_a_editar', {}):
                    qty_default = st.session_state['productos_a_editar'][sku]['quantity']
                    price_default = float(st.session_state['productos_a_editar'][sku]['price'])

                st.write(f"**{product_name}** (Costo: ${cost:,.2f})")
                cols = st.columns([1, 1])
                quantity = cols[0].number_input(f"Cantidad para {sku}", min_value=1, step=1, value=qty_default, key=f"qty_{sku}")
                price = cols[1].number_input(f"Precio Venta para {sku}", min_value=float(cost) + 0.01, format="%.2f", value=price_default, key=f"price_{sku}")
                products_to_add.append({"sku": sku, "quantity": quantity, "price": float(price)})

        submitted = st.form_submit_button("Previsualizar Cambios")

        if submitted:
            st.warning(f"**Estás a punto de {'ACTUALIZAR' if modo == 'Editar Licitación Existente' else 'CREAR'} la siguiente licitación:**")
            resumen_col1, resumen_col2 = st.columns(2)
            resumen_col1.write(f"**ID:** {tender_id}")
            resumen_col1.write(f"**Cliente:** {selected_client_name}")
            resumen_col2.write(f"**Fecha Creación:** {creation_date.strftime('%Y-%m-%d')}")
            resumen_col2.write(f"**Fecha Entrega:** {delivery_date.strftime('%Y-%m-%d')}")
            st.write("**Productos:**")
            preview_df = pd.DataFrame([{"Producto": p_name, "Cantidad": p_data['quantity'], "Precio": p_data['price']} for p_name, p_data in zip(selected_products, products_to_add)])
            st.dataframe(preview_df, hide_index=True)
            st.session_state['confirm_data'] = {"modo": modo, "tender_id": tender_id, "client_name": selected_client_name, "creation_date": creation_date, "delivery_date": delivery_date, "products": products_to_add}

    if 'confirm_data' in st.session_state and st.session_state['confirm_data']:
        if st.button("Confirmar y Guardar en Base de Datos", type="primary"):
            data = st.session_state['confirm_data']
            try:
                cursor = conn.cursor()
                client_id = clients_df[clients_df['nom_cli'] == data['client_name']]['id_cli'].iloc[0]
                if data['modo'] == "Crear Nueva Licitación":
                    cursor.execute("INSERT INTO public.tenders (id, id_cli, creation_date, delivery_date) VALUES (%s, %s, %s, %s);", (data['tender_id'], int(client_id), data['creation_date'], data['delivery_date']))
                else:
                    cursor.execute("UPDATE public.tenders SET id_cli=%s, creation_date=%s, delivery_date=%s WHERE id=%s;", (int(client_id), data['creation_date'], data['delivery_date'], data['tender_id']))
                    cursor.execute("DELETE FROM public.orders WHERE tender_id = %s;", (data['tender_id'],))
                for prod in data['products']:
                    order_id = f"{data['tender_id']}-{prod['sku']}"
                    cursor.execute("INSERT INTO public.orders (id, tender_id, product_id, quantity, price) VALUES (%s, %s, %s, %s, %s);", (order_id, data['tender_id'], prod['sku'], prod['quantity'], prod['price']))
                conn.commit()
                st.success(f"¡Licitación '{data['tender_id']}' guardada con éxito!")
                st.balloons()
            except Exception as e:
                conn.rollback()
                st.error(f"Error al guardar: {e}")
            finally:
                if 'cursor' in locals() and not cursor.closed:
                    cursor.close()
                st.session_state['confirm_data'] = None

def page_gestionar_clientes():
    st.title("👤 Gestionar Clientes")

    if 'editing_client_id' not in st.session_state:
        st.session_state.editing_client_id = None

    client_data_default = {'id_cli': None, 'nom_cli': '', 'rut_cli': ''}
    if st.session_state.editing_client_id is not None:
        client_data_default = load_data(f"SELECT * FROM public.clientes WHERE id_cli = {st.session_state.editing_client_id};").iloc[0]

    form_title = "Editar Cliente Existente" if st.session_state.editing_client_id else "Agregar Nuevo Cliente"
    with st.form("gestion_cliente_form"):
        st.subheader(form_title)
        nom_cli = st.text_input("Nombre del Cliente", value=client_data_default['nom_cli'])
        rut_cli = st.text_input("RUT del Cliente", value=client_data_default['rut_cli'], disabled=(st.session_state.editing_client_id is not None))
        
        submitted = st.form_submit_button("Previsualizar Cambios")
        if submitted:
            modo = "Editar" if st.session_state.editing_client_id else "Crear"
            st.warning(f"**Estás a punto de {'ACTUALIZAR' if modo == 'Editar' else 'CREAR'} el siguiente cliente:**")
            st.write(f"**Nombre:** {nom_cli}")
            st.write(f"**RUT:** {rut_cli}")
            
            st.session_state['confirm_client_data'] = {
                "modo": modo, "id_cli": st.session_state.editing_client_id,
                "nom_cli": nom_cli, "rut_cli": rut_cli
            }

    if st.session_state.editing_client_id:
        if st.button("Cancelar Edición"):
            st.session_state.editing_client_id = None
            st.rerun()

    if 'confirm_client_data' in st.session_state and st.session_state['confirm_client_data']:
        if st.button("Confirmar y Guardar Cliente", type="primary"):
            data = st.session_state['confirm_client_data']
            if not data['nom_cli'] or not data['rut_cli']:
                st.error("Error: El nombre y el RUT son obligatorios.")
            elif data['modo'] == "Crear" and not validar_rut(data['rut_cli']):
                st.error(f"El RUT '{data['rut_cli']}' no es válido.")
            else:
                try:
                    cursor = conn.cursor()
                    if data['modo'] == "Crear":
                        cursor.execute("INSERT INTO public.clientes (id_cli, nom_cli, rut_cli) VALUES ((SELECT COALESCE(MAX(id_cli), 0) + 1 FROM public.clientes), %s, %s);", (data['nom_cli'], data['rut_cli']))
                    else:
                        cursor.execute("UPDATE public.clientes SET nom_cli = %s WHERE id_cli = %s;", (data['nom_cli'], data['id_cli']))
                    conn.commit()
                    st.success(f"Cliente '{data['nom_cli']}' guardado con éxito.")
                    st.session_state.editing_client_id = None
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error al guardar cliente: {e}")
                finally:
                    if 'cursor' in locals() and not cursor.closed:
                        cursor.close()
                    st.session_state['confirm_client_data'] = None
                    st.rerun()

    st.markdown("---")
    st.subheader("Listado de Clientes Existentes")
    clientes_df = load_data("SELECT id_cli, nom_cli, rut_cli FROM public.clientes ORDER BY nom_cli;")

    col_header1, col_header2, col_header3 = st.columns([3,2,1])
    col_header1.write("**Nombre**")
    col_header2.write("**RUT**")
    
    for index, row in clientes_df.iterrows():
        col1, col2, col3 = st.columns([3,2,1])
        col1.write(row['nom_cli'])
        col2.write(row['rut_cli'])
        if col3.button("Editar", key=f"edit_{row['id_cli']}"):
            st.session_state.editing_client_id = row['id_cli']
            st.rerun()

def page_gestionar_productos():
    st.title("📦 Gestionar Productos")

    if 'editing_product_sku' not in st.session_state:
        st.session_state.editing_product_sku = None

    product_data_default = {'sku_pro': '', 'nom_pro': '', 'cost_prp': 0.01}
    if st.session_state.editing_product_sku is not None:
        product_data_default = load_data(f"SELECT * FROM public.products WHERE sku_pro = '{st.session_state.editing_product_sku}';").iloc[0]

    form_title = "Editar Producto Existente" if st.session_state.editing_product_sku else "Agregar Nuevo Producto"
    with st.form("gestion_producto_form"):
        st.subheader(form_title)
        sku_pro = st.text_input("SKU del Producto (ID único)", value=product_data_default['sku_pro'], disabled=(st.session_state.editing_product_sku is not None))
        nom_pro = st.text_input("Nombre del Producto", value=product_data_default['nom_pro'])
        cost_prp = st.number_input("Costo del Producto ($)", min_value=0.01, value=float(product_data_default['cost_prp']), format="%.2f")
        
        submitted = st.form_submit_button("Previsualizar Cambios")
        if submitted:
            modo = "Editar" if st.session_state.editing_product_sku else "Crear"
            st.warning(f"**Estás a punto de {'ACTUALIZAR' if modo == 'Editar' else 'CREAR'} el siguiente producto:**")
            st.write(f"**SKU:** {sku_pro}")
            st.write(f"**Nombre:** {nom_pro}")
            st.write(f"**Costo:** ${cost_prp:,.2f}")

            st.session_state['confirm_product_data'] = {
                "modo": modo, "sku_pro": sku_pro,
                "nom_pro": nom_pro, "cost_prp": cost_prp
            }

    if st.session_state.editing_product_sku:
        if st.button("Cancelar Edición"):
            st.session_state.editing_product_sku = None
            st.rerun()

    if 'confirm_product_data' in st.session_state and st.session_state['confirm_product_data']:
        if st.button("Confirmar y Guardar Producto", type="primary"):
            data = st.session_state['confirm_product_data']
            if not data['sku_pro'] or not data['nom_pro']:
                st.error("Error: El SKU y el nombre son obligatorios.")
            else:
                try:
                    cursor = conn.cursor()
                    if data['modo'] == "Crear":
                        cursor.execute("INSERT INTO public.products (sku_pro, nom_pro, cost_prp) VALUES (%s, %s, %s);", (data['sku_pro'], data['nom_pro'], data['cost_prp']))
                    else: # Modo Editar
                        cursor.execute("UPDATE public.products SET nom_pro = %s, cost_prp = %s WHERE sku_pro = %s;", (data['nom_pro'], data['cost_prp'], data['sku_pro']))
                    conn.commit()
                    st.success(f"Producto '{data['nom_pro']}' guardado con éxito.")
                    st.session_state.editing_product_sku = None
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error al guardar producto: {e}")
                finally:
                    if 'cursor' in locals() and not cursor.closed:
                        cursor.close()
                    st.session_state['confirm_product_data'] = None
                    st.rerun()

    st.markdown("---")
    st.subheader("Listado de Productos Existentes")
    productos_df = load_data("SELECT sku_pro, nom_pro, cost_prp FROM public.products ORDER BY nom_pro;")
    
    col_h1, col_h2, col_h3, col_h4 = st.columns([2,3,1,1])
    col_h1.write("**SKU**")
    col_h2.write("**Nombre**")
    col_h3.write("**Costo**")

    for index, row in productos_df.iterrows():
        c1, c2, c3, c4 = st.columns([2,3,1,1])
        c1.write(row['sku_pro'])
        c2.write(row['nom_pro'])
        c3.write(f"${row['cost_prp']:,.2f}")
        if c4.button("Editar", key=f"edit_prod_{row['sku_pro']}"):
            st.session_state.editing_product_sku = row['sku_pro']
            st.rerun()

# --- NAVEGACIÓN PRINCIPAL (SIDEBAR) ---
st.sidebar.title("Menú de Navegación")
selection = st.sidebar.radio(
    "Ir a:",
    ["Dashboard", "Ver Licitaciones", "Gestionar Licitaciones", "Gestionar Clientes", "Gestionar Productos"]
)

if "previous_selection" not in st.session_state:
    st.session_state.previous_selection = selection

if st.session_state.previous_selection != selection:
    st.cache_data.clear()
    st.session_state.previous_selection = selection
    st.toast(f"Cargando datos frescos para '{selection}'...", icon="🔄")

# Router para mostrar la página seleccionada
if selection == "Dashboard":
    page_dashboard()
elif selection == "Ver Licitaciones":
    page_ver_licitaciones()
elif selection == "Gestionar Licitaciones":
    page_gestionar_licitacion()
elif selection == "Gestionar Clientes":
    page_gestionar_clientes()
elif selection == "Gestionar Productos":
    page_gestionar_productos()