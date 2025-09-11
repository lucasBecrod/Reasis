# GUÍA DE ACCESO - BASE DE DATOS NACIONAL MINEDU

## 📋 INFORMACIÓN GENERAL

**Base de Datos**: Padrón Nacional de Instituciones Educativas  
**Organismo**: Ministerio de Educación del Perú (MINEDU)  
**Sistema**: ESCALE (Estadística de la Calidad Educativa)  
**Formato**: Archivos DBF (dBase IV)  
**Frecuencia**: Actualización mensual  

---

## 🌐 ACCESO Y DESCARGA

### Portal Oficial
- **URL Principal**: `http://escale.minedu.gob.pe/`
- **Sección**: Padrones y Centros de Costo
- **Subsección**: Padrón de Instituciones Educativas

### Ruta de Navegación Típica
1. Acceder a portal ESCALE
2. Ir a "Padrones" → "Padrón de Instituciones Educativas"
3. Seleccionar "Descargar padrón actualizado"
4. Elegir formato: **DBF (recomendado)** o Excel
5. Descargar archivo comprimido (.zip)

### URLs Directas (Verificar Disponibilidad)
```
# URL típica de descarga (formato puede variar)
http://escale.minedu.gob.pe/downloads/padron/Padron_web_YYYYMMDD.zip

# Ejemplo (verificar fecha actual)
http://escale.minedu.gob.pe/downloads/padron/Padron_web_20250731.zip
```

---

## 📁 ESTRUCTURA DEL ARCHIVO DESCARGADO

### Contenido del ZIP
```
Padron_web_20250731.zip
├── Padron_web.dbf                           # ARCHIVO PRINCIPAL (280+ MB)
├── Padlocaladi_web.dbf                      # Datos adicionales de locales
├── Instituciones_apoyo.dbf                  # Instituciones de apoyo
├── Especificacion de la tabla de datos padron web.xlsx
└── Especificacion de la tabla de datos locales adicionales.xlsx
```

### Descripción de Archivos

#### 1. **Padron_web.dbf** (Archivo Principal)
- **Registros**: ~179,000 instituciones educativas
- **Tamaño**: 283+ MB
- **Contenido**: Datos completos de todas las IIEE del país

#### 2. **Padlocaladi_web.dbf**
- **Registros**: ~90,000 locales educativos
- **Contenido**: Información adicional de infraestructura y localización

#### 3. **Instituciones_apoyo.dbf**
- **Contenido**: Instituciones de apoyo y servicios especializados

---

## 🔧 ESPECIFICACIÓN TÉCNICA

### Campos Principales - Padron_web.dbf

| **Campo** | **Tipo** | **Longitud** | **Descripción** |
|-----------|----------|--------------|-----------------|
| `CODINST` | C | 8 | Código de institución |
| `COD_MOD` | C | 7 | **Código modular** ⭐ |
| `ANEXO` | C | 1 | Anexo |
| `CODLOCAL` | C | 6 | Código de local educativo |
| `CEN_EDU` | C | 100 | **Nombre del servicio educativo** ⭐ |
| `NIV_MOD` | C | 2 | Código de nivel/modalidad |
| `D_NIV_MOD` | C | 50 | Nivel/modalidad |
| `D_FORMA` | C | 20 | Forma de atención |
| `TIPSSEXO` | C | 1 | Código de género |
| `D_TIPSSEXO` | C | 15 | Género de los alumnos |
| `GESTION` | C | 1 | Código de gestión |
| `D_GESTION` | C | 50 | Gestión del servicio educativo |
| `DIRECTOR` | C | 90 | Nombre del director |
| `TELEFONO` | C | 40 | Teléfono |
| `EMAIL` | C | 50 | Correo electrónico |
| `DIR_CEN` | C | 200 | **Dirección del local** ⭐ |
| `LOCALIDAD` | C | 80 | Localidad |
| `CEN_POB` | C | 100 | Centro poblado |
| `AREA_CENSO` | C | 5 | Código área geográfica |
| `DAREACENSO` | C | 12 | Detalle área geográfica |
| `CODGEO` | C | 6 | Código ubicación geográfica |
| `D_DPTO` | C | 15 | **Departamento** ⭐ |
| `D_PROV` | C | 40 | **Provincia** ⭐ |
| `D_DIST` | C | 60 | **Distrito** ⭐ |
| `D_REGION` | C | 50 | Dirección regional de educación |
| `CODOOII` | C | 6 | Código DRE/UGEL |
| `D_DREUGEL` | C | 60 | Nombre DRE/UGEL |
| `NLAT_IE` | N | 12 | Latitud |
| `NLONG_IE` | N | 12 | Longitud |
| `ESTADO` | C | 1 | **Código estado** ⭐ |
| `D_ESTADO` | C | 12 | **Estado del servicio** ⭐ |
| `TALUMNO` | N | 7 | Total alumnos |
| `TDOCENTE` | N | 6 | Total docentes |
| `TSECCION` | N | 5 | Total secciones |
| `FECHA_ACT` | C | 10 | Fecha actualización |

⭐ = Campos más importantes para vinculación

### Campos Clave para Búsquedas

#### Identificación:
- `COD_MOD`: Código modular único (7 dígitos)
- `CODLOCAL`: Código local educativo (6 dígitos)
- `CODINST`: Código institución (8 dígitos)

#### Nombres:
- `CEN_EDU`: Nombre/número oficial de la IE
- `DIR_CEN`: Dirección física del local

#### Ubicación:
- `D_DPTO`, `D_PROV`, `D_DIST`: Ubicación política
- `LOCALIDAD`, `CEN_POB`: Ubicación específica

#### Estado:
- `ESTADO`: "1" = Activa, "0" = Inactiva
- `D_ESTADO`: "Activa" / "Inactiva"

---

## 💻 IMPLEMENTACIÓN TÉCNICA

### Instalación de Dependencias
```bash
# Instalar librerías necesarias
pip install dbfread pandas

# Opcional para búsquedas avanzadas
pip install fuzzywuzzy python-levenshtein
```

### Script de Carga Básico
```python
from dbfread import DBF
import pandas as pd

def cargar_padron_minedu(ruta_archivo):
    """
    Carga el padrón nacional MINEDU desde archivo DBF
    
    Args:
        ruta_archivo (str): Ruta al archivo Padron_web.dbf
        
    Returns:
        DBF: Objeto tabla para iteración
        pandas.DataFrame: DataFrame opcional para análisis
    """
    
    # Cargar como objeto DBF (recomendado para archivos grandes)
    tabla_dbf = DBF(ruta_archivo, encoding='latin-1')
    
    print(f"Padrón cargado exitosamente:")
    print(f"  - Total registros: {len(tabla_dbf):,}")
    print(f"  - Campos disponibles: {len(tabla_dbf.field_names)}")
    
    return tabla_dbf

def convertir_a_dataframe(tabla_dbf, muestra=None):
    """
    Convierte tabla DBF a pandas DataFrame
    
    Args:
        tabla_dbf: Objeto DBF cargado
        muestra (int): Número de registros a cargar (None = todos)
    
    Returns:
        pandas.DataFrame: Datos en formato DataFrame
    """
    
    registros = []
    contador = 0
    
    for record in tabla_dbf:
        registros.append(dict(record))
        contador += 1
        
        if muestra and contador >= muestra:
            break
            
        if contador % 50000 == 0:
            print(f"  Procesados {contador:,} registros...")
    
    df = pd.DataFrame(registros)
    print(f"DataFrame creado: {len(df):,} filas × {len(df.columns)} columnas")
    
    return df

# Ejemplo de uso
ruta = r"C:\ruta\a\Padron_web.dbf"
tabla = cargar_padron_minedu(ruta)

# Cargar muestra para exploración
df_muestra = convertir_a_dataframe(tabla, muestra=10000)
```

### Script de Búsqueda Optimizada
```python
def buscar_institucion(tabla_dbf, criterios):
    """
    Busca instituciones en el padrón por múltiples criterios
    
    Args:
        tabla_dbf: Tabla DBF cargada
        criterios (dict): Criterios de búsqueda
            - 'codigo_modular': str
            - 'nombre': str  
            - 'departamento': str
            - 'activa_solo': bool
    
    Returns:
        list: Lista de instituciones encontradas
    """
    
    resultados = []
    
    for record in tabla_dbf:
        # Filtrar por estado (solo activas)
        if criterios.get('activa_solo', True):
            if record.get('ESTADO') != '1':
                continue
        
        # Filtrar por código modular exacto
        if criterios.get('codigo_modular'):
            if record.get('COD_MOD', '').strip() == criterios['codigo_modular']:
                resultados.append(dict(record))
                continue
        
        # Filtrar por nombre (contiene)
        if criterios.get('nombre'):
            nombre_ie = record.get('CEN_EDU', '').upper()
            if criterios['nombre'].upper() in nombre_ie:
                resultados.append(dict(record))
                continue
        
        # Filtrar por departamento
        if criterios.get('departamento'):
            depto = record.get('D_DPTO', '').upper()
            if criterios['departamento'].upper() in depto:
                resultados.append(dict(record))
                continue
    
    print(f"Búsqueda completada: {len(resultados)} resultados")
    return resultados

# Ejemplos de búsqueda
# Por código modular
resultado = buscar_institucion(tabla, {'codigo_modular': '0488403'})

# Por nombre
resultado = buscar_institucion(tabla, {'nombre': 'CAPTUY'})

# Por departamento
resultado = buscar_institucion(tabla, {'departamento': 'ANCASH'})
```

### Índice de Búsqueda Rápida
```python
def crear_indice_busqueda(tabla_dbf):
    """
    Crea índices en memoria para búsquedas rápidas
    
    Returns:
        dict: Diccionarios de índices por diferentes campos
    """
    
    indices = {
        'por_codigo_modular': {},
        'por_codigo_local': {},
        'por_nombre': {},
        'por_departamento': {}
    }
    
    print("Creando índices de búsqueda...")
    contador = 0
    
    for record in tabla_dbf:
        contador += 1
        if contador % 50000 == 0:
            print(f"  Indexados {contador:,} registros...")
        
        # Índice por código modular
        cod_mod = record.get('COD_MOD', '').strip()
        if cod_mod:
            indices['por_codigo_modular'][cod_mod] = dict(record)
        
        # Índice por código local
        cod_local = record.get('CODLOCAL', '').strip()
        if cod_local:
            indices['por_codigo_local'][cod_local] = dict(record)
        
        # Índice por nombre (normalizado)
        nombre = record.get('CEN_EDU', '').upper().strip()
        if nombre:
            indices['por_nombre'][nombre] = dict(record)
        
        # Índice por departamento
        depto = record.get('D_DPTO', '').upper().strip()
        if depto:
            if depto not in indices['por_departamento']:
                indices['por_departamento'][depto] = []
            indices['por_departamento'][depto].append(dict(record))
    
    print(f"Índices creados:")
    for tipo, indice in indices.items():
        print(f"  - {tipo}: {len(indice):,} entradas")
    
    return indices

# Uso de índices para búsqueda rápida
indices = crear_indice_busqueda(tabla)

# Búsqueda instantánea por código
institucion = indices['por_codigo_modular'].get('0488403')
if institucion:
    print(f"Encontrada: {institucion['CEN_EDU']}")
```

---

## 📊 CASOS DE USO COMUNES

### 1. Verificación de Código Modular
```python
def verificar_codigo_modular(indices, codigo):
    """Verifica si un código modular existe y está activo"""
    
    institucion = indices['por_codigo_modular'].get(codigo)
    
    if not institucion:
        return {"existe": False, "mensaje": "Código no encontrado"}
    
    activa = institucion.get('ESTADO') == '1'
    
    return {
        "existe": True,
        "activa": activa,
        "nombre": institucion.get('CEN_EDU'),
        "ubicacion": f"{institucion.get('D_DIST')}, {institucion.get('D_DPTO')}",
        "datos_completos": institucion
    }

# Ejemplo
resultado = verificar_codigo_modular(indices, '0488403')
print(resultado)
```

### 2. Búsqueda por Similitud de Nombres
```python
from fuzzywuzzy import fuzz, process

def buscar_por_similitud(indices, nombre_buscado, umbral=80):
    """Busca instituciones por similitud de nombres"""
    
    nombres_disponibles = list(indices['por_nombre'].keys())
    
    # Buscar los 5 nombres más similares
    matches = process.extract(
        nombre_buscado.upper(), 
        nombres_disponibles, 
        limit=5, 
        scorer=fuzz.ratio
    )
    
    resultados = []
    for nombre_match, score in matches:
        if score >= umbral:
            institucion = indices['por_nombre'][nombre_match]
            resultados.append({
                'score': score,
                'nombre_encontrado': nombre_match,
                'codigo_modular': institucion.get('COD_MOD'),
                'ubicacion': f"{institucion.get('D_DIST')}, {institucion.get('D_DPTO')}",
                'datos': institucion
            })
    
    return resultados

# Ejemplo
similares = buscar_por_similitud(indices, "CAPTUY", umbral=75)
for resultado in similares:
    print(f"Score: {resultado['score']}% - {resultado['nombre_encontrado']}")
```

### 3. Análisis Geográfico
```python
def analizar_por_departamento(indices, departamento):
    """Analiza instituciones por departamento"""
    
    instituciones = indices['por_departamento'].get(departamento.upper(), [])
    
    if not instituciones:
        return {"mensaje": "Departamento no encontrado"}
    
    # Estadísticas básicas
    total = len(instituciones)
    activas = len([i for i in instituciones if i.get('ESTADO') == '1'])
    
    # Distribución por gestión
    gestion = {}
    for inst in instituciones:
        tipo = inst.get('D_GESTION', 'No especificado')
        gestion[tipo] = gestion.get(tipo, 0) + 1
    
    return {
        "departamento": departamento,
        "total_instituciones": total,
        "activas": activas,
        "inactivas": total - activas,
        "distribucion_gestion": gestion
    }

# Ejemplo
estadisticas = analizar_por_departamento(indices, "ANCASH")
print(estadisticas)
```

---

## ⚠️ CONSIDERACIONES IMPORTANTES

### Limitaciones Técnicas
1. **Memoria RAM**: Archivo completo requiere 2-4 GB de RAM
2. **Tiempo de carga**: 5-15 minutos dependiendo del hardware
3. **Encoding**: Siempre usar `encoding='latin-1'` para caracteres especiales
4. **Actualizaciones**: Verificar mensualmente nuevas versiones

### Mejores Prácticas

#### Performance
- Usar índices en memoria para búsquedas repetitivas
- Procesar en lotes para operaciones masivas
- Filtrar por estado "Activa" si no se necesitan instituciones cerradas

#### Calidad de Datos
- Validar códigos modulares (7 dígitos numéricos)
- Normalizar nombres para comparaciones
- Verificar fechas de actualización

#### Backup y Versionado
- Mantener versiones anteriores del padrón
- Documentar cambios entre versiones
- Crear backups antes de actualizaciones masivas

---

## 📅 CRONOGRAMA DE ACTUALIZACIONES

### Frecuencia Oficial
- **Mensual**: Datos de matrícula y docentes
- **Trimestral**: Cambios estructurales importantes
- **Anual**: Revisión completa del padrón

### Fechas Típicas de Actualización
- **Enero**: Padrón inicial del año
- **Marzo**: Post-matrícula regular
- **Junio**: Mitad de año
- **Agosto**: Pre-censo educativo
- **Noviembre**: Cierre de año escolar

### Control de Versiones
```python
def verificar_version_padron(archivo_dbf):
    """Verifica la versión y fecha del padrón cargado"""
    
    # Buscar fecha más reciente en FECHA_ACT
    fechas = []
    contador = 0
    
    for record in archivo_dbf:
        fecha = record.get('FECHA_ACT')
        if fecha:
            fechas.append(fecha)
        
        contador += 1
        if contador >= 1000:  # Muestra representativa
            break
    
    if fechas:
        fecha_mas_reciente = max(fechas)
        return f"Versión del padrón: {fecha_mas_reciente}"
    
    return "Fecha de versión no disponible"

print(verificar_version_padron(tabla))
```

---

## 🔗 RECURSOS ADICIONALES

### Documentación Oficial
- **Portal ESCALE**: http://escale.minedu.gob.pe/
- **Manual de usuario**: Incluido en descarga (archivos Excel)
- **Soporte técnico**: Contactar MINEDU - Unidad de Estadística

### Herramientas Complementarias
- **DBF Viewer**: Para visualizar archivos DBF sin programar
- **LibreOffice Calc**: Puede abrir archivos DBF directamente
- **QGIS**: Para análisis geoespacial con coordenadas incluidas

### Comunidad y Soporte
- **Foros especializados**: Comunidades de análisis educativo en Perú
- **GitHub**: Repositorios con scripts similares
- **Stack Overflow**: Tags: python, dbf, education-data

---

## 📞 CONTACTOS DE SOPORTE

**MINEDU - Unidad de Estadística**
- **Web**: http://escale.minedu.gob.pe/
- **Email**: escale@minedu.gob.pe (verificar vigencia)
- **Teléfono**: Consultar en portal oficial

**Soporte Técnico DBF**
- **Librería dbfread**: https://github.com/olemb/dbfread
- **Documentación pandas**: https://pandas.pydata.org/

---

*Documento actualizado: 2025-08-09*  
*Última versión padrón verificada: 31-07-2025*  
*Proyecto: Reasis - Análisis Instituciones Educativas*