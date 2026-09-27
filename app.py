import sqlite3
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Base de datos SQLite
def init_db():
    conn = sqlite3.connect('negocio_gas.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio_compra REAL NOT NULL,
            precio_venta REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plantillas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plantilla_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plantilla_id INTEGER,
            producto_id INTEGER,
            cantidad REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            cliente TEXT,
            cobro_mano_obra REAL,
            pago_trabajadores REAL,
            gastos_varios REAL,
            costo_insumos REAL,
            cobro_insumos REAL,
            ingreso_total REAL,
            costo_operativo REAL,
            ganancia_limpia REAL,
            caja_insumos REAL,
            fondo_inversion REAL,
            caja_ahorro REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/productos', methods=['GET', 'POST'])
def gestionar_productos():
    conn = sqlite3.connect('negocio_gas.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        datos = request.json
        if 'id' in datos and datos['id']:
            cursor.execute("UPDATE productos SET nombre=?, precio_compra=?, precio_venta=? WHERE id=?",
                           (datos['nombre'], float(datos['precio_compra']), float(datos['precio_venta']), datos['id']))
        else:
            cursor.execute("INSERT INTO productos (nombre, precio_compra, precio_venta) VALUES (?, ?, ?)",
                           (datos['nombre'], float(datos['precio_compra']), float(datos['precio_venta'])))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    
    cursor.execute("SELECT id, nombre, precio_compra, precio_venta, (precio_venta - precio_compra) FROM productos ORDER BY nombre ASC")
    productos = [{"id": r[0], "nombre": r[1], "precio_compra": r[2], "precio_venta": r[3], "ganancia": r[4]} for r in cursor.fetchall()]
    conn.close()
    return jsonify(productos)

@app.route('/api/productos/<int:prod_id>', methods=['DELETE'])
def eliminar_producto(prod_id):
    conn = sqlite3.connect('negocio_gas.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/plantillas', methods=['GET', 'POST'])
def gestionar_plantillas():
    conn = sqlite3.connect('negocio_gas.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        datos = request.json
        plantilla_id = datos.get('id')
        if plantilla_id:
            cursor.execute("UPDATE plantillas SET nombre=? WHERE id=?", (datos['nombre'], plantilla_id))
            cursor.execute("DELETE FROM plantilla_items WHERE plantilla_id=?", (plantilla_id,))
        else:
            cursor.execute("INSERT INTO plantillas (nombre) VALUES (?)", (datos['nombre'],))
            plantilla_id = cursor.lastrowid

        for item in datos.get('items', []):
            cursor.execute("INSERT INTO plantilla_items (plantilla_id, producto_id, cantidad) VALUES (?, ?, ?)",
                           (plantilla_id, item['producto_id'], float(item['cantidad'])))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    
    cursor.execute("SELECT id, nombre FROM plantillas")
    plantillas = []
    for row in cursor.fetchall():
        p_id, p_nombre = row[0], row[1]
        c_items = conn.cursor()
        c_items.execute('''
            SELECT pi.producto_id, p.nombre, p.precio_compra, p.precio_venta, pi.cantidad 
            FROM plantilla_items pi 
            JOIN productos p ON pi.producto_id = p.id 
            WHERE pi.plantilla_id = ?
        ''', (p_id,))
        items = [{"producto_id": r[0], "nombre": r[1], "precio_compra": r[2], "precio_venta": r[3], "cantidad": r[4]} for r in c_items.fetchall()]
        plantillas.append({"id": p_id, "nombre": p_nombre, "items": items})
    conn.close()
    return jsonify(plantillas)

@app.route('/api/plantillas/<int:plantilla_id>', methods=['DELETE'])
def eliminar_plantilla(plantilla_id):
    conn = sqlite3.connect('negocio_gas.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM plantillas WHERE id = ?", (plantilla_id,))
    cursor.execute("DELETE FROM plantilla_items WHERE plantilla_id = ?", (plantilla_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/obras', methods=['GET', 'POST'])
def gestionar_obras():
    conn = sqlite3.connect('negocio_gas.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        d = request.json
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute('''
            INSERT INTO obras (fecha, cliente, cobro_mano_obra, pago_trabajadores, gastos_varios, 
                               costo_insumos, cobro_insumos, ingreso_total, costo_operativo, 
                               ganancia_limpia, caja_insumos, fondo_inversion, caja_ahorro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fecha, d['cliente'], d['cobro_mano_obra'], d['pago_trabajadores'], d['gastos_varios'],
              d['costo_insumos'], d['cobro_insumos'], d['ingreso_total'], d['costo_operativo'],
              d['ganancia_limpia'], d['caja_insumos'], d['fondo_inversion'], d['caja_ahorro']))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    
    cursor.execute("SELECT * FROM obras ORDER BY id DESC")
    columnas = [column[0] for column in cursor.description]
    obras = [dict(zip(columnas, row)) for row in cursor.fetchall()]
    conn.close()
    return jsonify(obras)

# --- INTERFAZ WEB ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>GAS LP GUANACASTE</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; background-color: #fcfbf4; color: #222; }
        .header { background: #fbc02d; color: #111; padding: 18px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 4px solid #f57f17; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 800; }
        .container { padding: 20px; max-width: 1100px; margin: 0 auto; }
        .card { background: white; padding: 22px; border-radius: 10px; box-shadow: 0 3px 10px rgba(0,0,0,0.06); margin-bottom: 20px; border-left: 5px solid #fbc02d; }
        h2 { color: #f57f17; margin-top: 0; border-bottom: 2px solid #fff59d; padding-bottom: 8px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        label { display: block; margin-top: 10px; font-weight: 700; font-size: 14px; }
        input, select { width: 100%; padding: 10px; margin-top: 4px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 6px; }
        button { background-color: #fbc02d; color: #111; border: none; padding: 11px 15px; border-radius: 6px; cursor: pointer; font-weight: bold; margin-top: 15px; width: 100%; font-size: 15px; }
        button:hover { background-color: #f57f17; color: white; }
        .btn-green { background-color: #2e7d32; color: white; }
        .btn-green:hover { background-color: #1b5e20; }
        .btn-warning { background-color: #f57f17; color: white; padding: 5px 10px; width: auto; font-size: 12px; margin-top:0; }
        .btn-danger { background-color: #d32f2f; color: white; padding: 5px 10px; width: auto; font-size: 12px; margin-top:0; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #e0e0e0; padding: 10px; text-align: left; font-size: 14px; }
        th { background-color: #fffde7; }
        .kpi-container { display: flex; gap: 15px; margin-top: 15px; }
        .kpi { flex: 1; background: #fffde7; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #fff59d; }
        .kpi h3 { margin: 0; font-size: 20px; color: #f57f17; }
        .kpi p { margin: 5px 0 0 0; font-size: 11px; font-weight: bold; color: #666; }
        .row-item { display: flex; gap: 10px; margin-top: 8px; align-items: center; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { background: #eee; color: #333; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; width: auto; font-weight: bold; }
        .tab-btn.active { background: #fbc02d; color: #111; }
    </style>
</head>
<body>

    <div class="header">
        <h1>GAS LP GUANACASTE</h1>
        <span>Control Financiero</span>
    </div>

    <div class="container">
        
        <div class="tabs">
            <button class="tab-btn active" onclick="verTab('tab_obra')">Nueva Instalación</button>
            <button class="tab-btn" onclick="verTab('tab_productos')">Catálogo de Insumos</button>
            <button class="tab-btn" onclick="verTab('tab_plantillas')">Plantillas Guardadas</button>
            <button class="tab-btn" onclick="verTab('tab_historial')">Historial de Trabajos</button>
        </div>

        <!-- TAB 1: REGISTRO DE INSTALACIÓN -->
        <div id="tab_obra" class="tab-content">
            <div class="card">
                <h2>Cargar Trabajo / Instalación</h2>
                <div class="grid">
                    <div>
                        <label>Cliente / Ubicación Obra:</label>
                        <input type="text" id="obra_cliente" placeholder="Ej: Cliente 01, Liberia">
                        <label>Plantilla Predeterminada:</label>
                        <select id="select_plantilla" onchange="cargarPlantillaEnObra()">
                            <option value="">-- Trabajo Personalizado --</option>
                        </select>
                    </div>
                    <div>
                        <label>Cobro Mano de Obra (₡):</label>
                        <input type="number" id="obra_mo" value="90000" oninput="actualizarCalculos()">
                        <label>Pago Trabajadores (₡):</label>
                        <input type="number" id="obra_trab" value="60000" oninput="actualizarCalculos()">
                        <label>Combustible y Varios (₡):</label>
                        <input type="number" id="obra_gastos" value="10000" oninput="actualizarCalculos()">
                    </div>
                </div>

                <h3>Insumos Utilizados</h3>
                <div id="lista_insumos_obra"></div>
                <button type="button" class="btn-green" onclick="agregarFilaInsumoObra()">+ Agregar Insumo</button>

                <div class="kpi-container">
                    <div class="kpi"><h3 id="res_ingreso">₡0</h3><p>INGRESO TOTAL</p></div>
                    <div class="kpi"><h3 id="res_costo">₡0</h3><p>SALARIOS Y COSTOS OPERATIVOS</p></div>
                    <div class="kpi" style="background:#e8f5e9;"><h3 id="res_ganancia" style="color:#2e7d32;">₡0</h3><p>GANANCIA REAL LIMPIA</p></div>
                </div>

                <div class="kpi-container" style="margin-top:10px;">
                    <div class="kpi"><h3 id="rep_insumos">₡0</h3><p>INSUMOS</p></div>
                    <div class="kpi"><h3 id="rep_inversion">₡0</h3><p>OTROS NEGOCIOS</p></div>
                    <div class="kpi"><h3 id="rep_ahorro">₡0</h3><p>AHORRO GAS</p></div>
                </div>

                <button onclick="guardarTrabajoEnHistorial()" class="btn-green" style="margin-top:20px; font-size:18px;">Guardar Trabajo en Historial</button>
            </div>
        </div>

        <!-- TAB 2: CATÁLOGO DE PRODUCTOS -->
        <div id="tab_productos" class="tab-content" style="display:none;">
            <div class="grid">
                <div class="card">
                    <h2 id="titulo_form_producto">Nuevo Insumo</h2>
                    <input type="hidden" id="p_id">
                    <label>Nombre del Insumo:</label>
                    <input type="text" id="p_nombre">
                    <label>Precio Compra (₡):</label>
                    <input type="number" id="p_compra">
                    <label>Precio Venta (₡):</label>
                    <input type="number" id="p_venta">
                    <button onclick="guardarProducto()" id="btn_guardar_p">Guardar En Base de Datos</button>
                    <button onclick="limpiarFormProducto()" style="background:#ccc; display:none;" id="btn_cancelar_p">Cancelar Edición</button>
                </div>
                <div class="card">
                    <h2>Insumos Registrados</h2>
                    <table>
                        <thead>
                            <tr><th>Nombre</th><th>Costo</th><th>Venta</th><th>Acciones</th></tr>
                        </thead>
                        <tbody id="tabla_productos"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 3: PLANTILLAS -->
        <div id="tab_plantillas" class="tab-content" style="display:none;">
            <div class="grid">
                <div class="card">
                    <h2 id="titulo_form_plantilla">Crear / Editar Plantilla</h2>
                    <input type="hidden" id="plantilla_id">
                    <label>Nombre de la Plantilla:</label>
                    <input type="text" id="plantilla_nombre" placeholder="Ej: Instalación Completa Certificada">
                    <h3>Insumos de la Plantilla</h3>
                    <div id="items_plantilla"></div>
                    <button type="button" class="btn-green" onclick="agregarFilaPlantilla()">+ Agregar Insumo</button>
                    <button onclick="guardarPlantilla()" style="margin-top:15px;">Guardar Configuración</button>
                    <button onclick="limpiarFormPlantilla()" style="background:#ccc; display:none;" id="btn_cancelar_plantilla">Cancelar Edición</button>
                </div>
                <div class="card">
                    <h2>Plantillas Existentes</h2>
                    <table>
                        <thead>
                            <tr><th>Nombre</th><th>Insumos</th><th>Acciones</th></tr>
                        </thead>
                        <tbody id="tabla_plantillas_lista"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 4: HISTORIAL -->
        <div id="tab_historial" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Resumen General de Ingresos</h2>
                <div class="kpi-container">
                    <div class="kpi"><h3 id="tot_semana">₡0</h3><p>GANANCIA ESTA SEMANA</p></div>
                    <div class="kpi"><h3 id="tot_mes">₡0</h3><p>GANANCIA ESTE MES</p></div>
                    <div class="kpi" style="background:#e8f5e9;"><h3 id="tot_general" style="color:#2e7d32;">₡0</h3><p>GANANCIA HISTÓRICA TOTAL</p></div>
                </div>
                <br>
                <h2>Historial Detallado de Trabajos</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Cliente</th>
                            <th>Ingreso Total</th>
                            <th>Costo Operativo</th>
                            <th>Ganancia Limpia</th>
                            <th>Caja Insumos</th>
                            <th>Inversión</th>
                            <th>Ahorro</th>
                        </tr>
                    </thead>
                    <tbody id="tabla_historial"></tbody>
                </table>
            </div>
        </div>

    </div>

    <script>
        let productos = [];
        let plantillas = [];
        let calculoActual = {};

        function verTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(d => d.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).style.display = 'block';
            event.target.classList.add('active');
        }

        async function cargarTodo() {
            const rProd = await fetch('/api/productos');
            productos = await rProd.json();
            renderProductos();

            const rPlan = await fetch('/api/plantillas');
            plantillas = await rPlan.json();
            renderPlantillasSelect();
            renderTablaPlantillas();

            cargarHistorial();
        }

        // --- PRODUCTOS ---
        function renderProductos() {
            const tb = document.getElementById('tabla_productos');
            tb.innerHTML = '';
            productos.forEach(p => {
                tb.innerHTML += `<tr>
                    <td><b>${p.nombre}</b></td>
                    <td>₡${p.precio_compra.toLocaleString()}</td>
                    <td>₡${p.precio_venta.toLocaleString()}</td>
                    <td>
                        <button class="btn-warning" onclick="editarProducto(${p.id})">Editar</button>
                        <button class="btn-danger" onclick="eliminarProducto(${p.id})">x</button>
                    </td>
                </tr>`;
            });
        }

        function editarProducto(id) {
            const p = productos.find(x => x.id == id);
            if(p) {
                document.getElementById('p_id').value = p.id;
                document.getElementById('p_nombre').value = p.nombre;
                document.getElementById('p_compra').value = p.precio_compra;
                document.getElementById('p_venta').value = p.precio_venta;
                document.getElementById('titulo_form_producto').innerText = 'Editar Insumo';
                document.getElementById('btn_guardar_p').innerText = 'Actualizar Insumo';
                document.getElementById('btn_cancelar_p').style.display = 'block';
            }
        }

        function limpiarFormProducto() {
            document.getElementById('p_id').value = '';
            document.getElementById('p_nombre').value = '';
            document.getElementById('p_compra').value = '';
            document.getElementById('p_venta').value = '';
            document.getElementById('titulo_form_producto').innerText = 'Nuevo Insumo';
            document.getElementById('btn_guardar_p').innerText = 'Guardar En Base de Datos';
            document.getElementById('btn_cancelar_p').style.display = 'none';
        }

        async function guardarProducto() {
            const id = document.getElementById('p_id').value;
            await fetch('/api/productos', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    id: id ? parseInt(id) : null,
                    nombre: document.getElementById('p_nombre').value,
                    precio_compra: document.getElementById('p_compra').value,
                    precio_venta: document.getElementById('p_venta').value
                })
            });
            limpiarFormProducto();
            cargarTodo();
        }

        async function eliminarProducto(id) {
            if(confirm('¿Seguro de eliminar este insumo?')) {
                await fetch(`/api/productos/${id}`, { method: 'DELETE' });
                cargarTodo();
            }
        }

        // --- INSTALACIÓN ---
        function agregarFilaInsumoObra(prodId = '', cantidad = 1) {
            const div = document.getElementById('lista_insumos_obra');
            const rId = Date.now() + Math.random();
            let opt = '<option value="">-- Seleccionar Insumo --</option>';
            productos.forEach(p => {
                opt += `<option value="${p.id}" ${p.id == prodId ? 'selected' : ''}>${p.nombre} (Venta: ₡${p.precio_venta})</option>`;
            });

            const html = `
                <div class="row-item" id="row_${rId}">
                    <select id="sel_${rId}" onchange="actualizarCalculos()">${opt}</select>
                    <input type="number" id="cant_${rId}" value="${cantidad}" placeholder="Cant." style="width:100px;" oninput="actualizarCalculos()">
                    <button type="button" class="btn-danger" onclick="document.getElementById('row_${rId}').remove(); actualizarCalculos();">x</button>
                </div>
            `;
            div.insertAdjacentHTML('beforeend', html);
            actualizarCalculos();
        }

        function actualizarCalculos() {
            let costoInsumos = 0;
            let cobroInsumos = 0;

            document.querySelectorAll('#lista_insumos_obra .row-item').forEach(r => {
                const id = r.id.replace('row_', '');
                const pId = document.getElementById(`sel_${id}`).value;
                const cant = parseFloat(document.getElementById(`cant_${id}`).value) || 0;
                
                const p = productos.find(x => x.id == pId);
                if(p) {
                    costoInsumos += p.precio_compra * cant;
                    cobroInsumos += p.precio_venta * cant;
                }
            });

            const mo = parseFloat(document.getElementById('obra_mo').value) || 0;
            const trab = parseFloat(document.getElementById('obra_trab').value) || 0;
            const gastos = parseFloat(document.getElementById('obra_gastos').value) || 0;

            const ingresoTotal = mo + cobroInsumos;
            const costoOperativo = trab + gastos + costoInsumos;
            const gananciaLimpia = ingresoTotal - costoOperativo;

            const cInsumos = costoInsumos + (gananciaLimpia * 0.40);
            const fInversion = gananciaLimpia * 0.30;
            const cAhorro = gananciaLimpia * 0.30;

            document.getElementById('res_ingreso').innerText = '₡' + ingresoTotal.toLocaleString();
            document.getElementById('res_costo').innerText = '₡' + costoOperativo.toLocaleString();
            document.getElementById('res_ganancia').innerText = '₡' + gananciaLimpia.toLocaleString();

            document.getElementById('rep_insumos').innerText = '₡' + cInsumos.toLocaleString();
            document.getElementById('rep_inversion').innerText = '₡' + fInversion.toLocaleString();
            document.getElementById('rep_ahorro').innerText = '₡' + cAhorro.toLocaleString();

            calculoActual = {
                cliente: document.getElementById('obra_cliente').value || 'Cliente Particular',
                cobro_mano_obra: mo,
                pago_trabajadores: trab,
                gastos_varios: gastos,
                costo_insumos: costoInsumos,
                cobro_insumos: cobroInsumos,
                ingreso_total: ingresoTotal,
                costo_operativo: costoOperativo,
                ganancia_limpia: gananciaLimpia,
                caja_insumos: cInsumos,
                fondo_inversion: fInversion,
                caja_ahorro: cAhorro
            };
        }

        async function guardarTrabajoEnHistorial() {
            if(!calculoActual.ingreso_total) {
                alert('No hay datos para guardar');
                return;
            }
            await fetch('/api/obras', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(calculoActual)
            });
            alert('Instalación guardada exitosamente');
            document.getElementById('lista_insumos_obra').innerHTML = '';
            document.getElementById('obra_cliente').value = '';
            actualizarCalculos();
            cargarHistorial();
        }

        // --- PLANTILLAS ---
        function renderPlantillasSelect() {
            const sel = document.getElementById('select_plantilla');
            sel.innerHTML = '<option value="">-- Trabajo Personalizado --</option>';
            plantillas.forEach(p => {
                sel.innerHTML += `<option value="${p.id}">${p.nombre}</option>`;
            });
        }

        function renderTablaPlantillas() {
            const tb = document.getElementById('tabla_plantillas_lista');
            tb.innerHTML = '';
            plantillas.forEach(p => {
                tb.innerHTML += `<tr>
                    <td><b>${p.nombre}</b></td>
                    <td>${p.items.length} insumos</td>
                    <td>
                        <button class="btn-warning" onclick="editarPlantilla(${p.id})">Editar</button>
                        <button class="btn-danger" onclick="eliminarPlantilla(${p.id})">x</button>
                    </td>
                </tr>`;
            });
        }

        function editarPlantilla(id) {
            const pl = plantillas.find(x => x.id == id);
            if(pl) {
                document.getElementById('plantilla_id').value = pl.id;
                document.getElementById('plantilla_nombre').value = pl.nombre;
                document.getElementById('items_plantilla').innerHTML = '';
                
                pl.items.forEach(item => {
                    agregarFilaPlantilla(item.producto_id, item.cantidad);
                });

                document.getElementById('titulo_form_plantilla').innerText = 'Editar Plantilla';
                document.getElementById('btn_cancelar_plantilla').style.display = 'block';
            }
        }

        function limpiarFormPlantilla() {
            document.getElementById('plantilla_id').value = '';
            document.getElementById('plantilla_nombre').value = '';
            document.getElementById('items_plantilla').innerHTML = '';
            document.getElementById('titulo_form_plantilla').innerText = 'Crear Plantilla';
            document.getElementById('btn_cancelar_plantilla').style.display = 'none';
        }

        function cargarPlantillaEnObra() {
            const id = document.getElementById('select_plantilla').value;
            document.getElementById('lista_insumos_obra').innerHTML = '';
            const pl = plantillas.find(x => x.id == id);
            if(pl) {
                pl.items.forEach(item => {
                    agregarFilaInsumoObra(item.producto_id, item.cantidad);
                });
            }
        }

        function agregarFilaPlantilla(prodId = '', cantidad = 1) {
            const div = document.getElementById('items_plantilla');
            const rId = Date.now() + Math.random();
            let opt = '<option value="">-- Seleccionar Insumo --</option>';
            productos.forEach(p => { 
                opt += `<option value="${p.id}" ${p.id == prodId ? 'selected' : ''}>${p.nombre}</option>`; 
            });

            div.insertAdjacentHTML('beforeend', `
                <div class="row-item" id="p_row_${rId}">
                    <select id="p_sel_${rId}">${opt}</select>
                    <input type="number" id="p_cant_${rId}" value="${cantidad}" placeholder="Cant." style="width:100px;">
                    <button type="button" class="btn-danger" onclick="document.getElementById('p_row_${rId}').remove();">x</button>
                </div>
            `);
        }

        async function guardarPlantilla() {
            const items = [];
            document.querySelectorAll('#items_plantilla .row-item').forEach(r => {
                const id = r.id.replace('p_row_', '');
                items.push({
                    producto_id: document.getElementById(`p_sel_${id}`).value,
                    cantidad: document.getElementById(`p_cant_${id}`).value
                });
            });

            const pId = document.getElementById('plantilla_id').value;

            await fetch('/api/plantillas', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    id: pId ? parseInt(pId) : null,
                    nombre: document.getElementById('plantilla_nombre').value,
                    items: items
                })
            });
            alert('Plantilla guardada');
            limpiarFormPlantilla();
            cargarTodo();
        }

        async function eliminarPlantilla(id) {
            if(confirm('¿Seguro de eliminar esta plantilla?')) {
                await fetch(`/api/plantillas/${id}`, { method: 'DELETE' });
                cargarTodo();
            }
        }

        // --- HISTORIAL Y ACUMULADOS ---
        async function cargarHistorial() {
            const res = await fetch('/api/obras');
            const data = await res.json();
            const tb = document.getElementById('tabla_historial');
            tb.innerHTML = '';

            let totalHist = 0;
            let totalMes = 0;
            let totalSemana = 0;

            const ahora = new Date();
            const haceSieteDias = new Date();
            haceSieteDias.setDate(ahora.getDate() - 7);

            const mesActual = ahora.getMonth();
            const anioActual = ahora.getFullYear();

            data.forEach(o => {
                const ganancia = o.ganancia_limpia || 0;
                totalHist += ganancia;

                const fechaObra = new Date(o.fecha.replace(' ', 'T'));
                
                if(!isNaN(fechaObra.getTime())) {
                    if(fechaObra >= haceSieteDias) {
                        totalSemana += ganancia;
                    }
                    if(fechaObra.getMonth() === mesActual && fechaObra.getFullYear() === anioActual) {
                        totalMes += ganancia;
                    }
                }

                tb.innerHTML += `<tr>
                    <td>${o.fecha}</td>
                    <td>${o.cliente}</td>
                    <td>₡${o.ingreso_total.toLocaleString()}</td>
                    <td>₡${o.costo_operativo.toLocaleString()}</td>
                    <td style="font-weight:bold; color:green;">₡${ganancia.toLocaleString()}</td>
                    <td>₡${o.caja_insumos.toLocaleString()}</td>
                    <td>₡${o.fondo_inversion.toLocaleString()}</td>
                    <td>₡${o.caja_ahorro.toLocaleString()}</td>
                </tr>`;
            });

            document.getElementById('tot_semana').innerText = '₡' + totalSemana.toLocaleString();
            document.getElementById('tot_mes').innerText = '₡' + totalMes.toLocaleString();
            document.getElementById('tot_general').innerText = '₡' + totalHist.toLocaleString();
        }

        window.onload = cargarTodo;
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5001)