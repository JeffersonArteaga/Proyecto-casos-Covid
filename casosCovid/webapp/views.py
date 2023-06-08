import numpy as np
from django.http import HttpResponseRedirect
from django.shortcuts import render
import pandas as pd
from django.urls import reverse
from sodapy import Socrata
from statistics import mode
import matplotlib.pyplot as plt
import io
import base64

client = Socrata ("www.datos.gov.co", None)
# Create your views here.

def graficaLineaFrecuencia(frecuencia_edad):
    # Calcular los rangos de edades
    edades = frecuencia_edad.index.astype(int)
    rango_min = min(edades)
    rango_max = max(edades)
    rango_inicio = rango_min - (rango_min % 5)  # Ajustar el rango de inicio al múltiplo de 5 anterior
    rango_fin = rango_max + (5 - rango_max % 5)  # Ajustar el rango de fin al múltiplo de 5 siguiente
    rangos_edades = np.arange(rango_inicio, rango_fin + 1, 5)  # Rangos de 5 en 5

    # Calcular la frecuencia por rango de edades
    frecuencia_rangos = []
    for i in range(len(rangos_edades) - 1):
        rango_inicio = rangos_edades[i]
        rango_fin = rangos_edades[i + 1]
        frecuencia_rango = frecuencia_edad[(edades >= rango_inicio) & (edades < rango_fin)].sum()
        frecuencia_rangos.append(frecuencia_rango)

    plt.figure(figsize=(18, 6))  # Ajustar el tamaño del gráfico

    # Crear un gráfico de línea con puntos para mostrar la frecuencia de edad por rangos
    plt.plot(rangos_edades[:-1], frecuencia_rangos, marker='o', linestyle='-', linewidth=2)

    # Configurar los ejes y el título del gráfico
    plt.xlabel('Rango de Edades')
    plt.ylabel('Numero total de casos')
    plt.title('Numero total de casos por Edad en Rangos de 5 años')

    # Establecer las etiquetas del eje x con los rangos de edades
    etiquetas = [f'{rango}-{rango + 4}' for rango in rangos_edades[:-1]]
    plt.xticks(rangos_edades[:-1], etiquetas)

    # Guardar la gráfica como una imagen en memoria
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)

    # Codificar la imagen en base64
    imagen_base64 = base64.b64encode(buffer.read()).decode()
    return imagen_base64

def graficaAnilloFrecuencia(datos_frecuencia, titulo, leyenda2):
    municipios = datos_frecuencia.index
    frecuencias = datos_frecuencia.values
    plt.figure(figsize=(10, 6))
    # Configuración del gráfico de anillo
    wedges, texts, autotexts = plt.pie(frecuencias, autopct='', startangle=90,
                                       counterclock=False, wedgeprops=dict(width=0.4), textprops={'fontsize': 10})
    plt.setp(autotexts, size=8, weight='bold')
    plt.title(titulo)
    # Crear un círculo blanco en el centro para formar un anillo
    centro_circulo = plt.Circle((0, 0), 0.3, color='white')
    fig = plt.gcf()
    fig.gca().add_artist(centro_circulo)
    # Crear la lista de colores relacionada a cada municipio
    lista_colores = [w.get_facecolor()[0] for w in wedges]
    # Calcular los porcentajes nuevamente
    total_frecuencias = sum(frecuencias)
    porcentajes = [frecuencia / total_frecuencias * 100 for frecuencia in frecuencias]
    # Crear la leyenda con porcentajes y municipios
    leyenda = [f'{municipio} {porcentaje:.3f}%' for porcentaje, municipio in zip(porcentajes, municipios)]
    plt.legend(leyenda, loc='center left', bbox_to_anchor=(1, 0.5), title=leyenda2,
               labelspacing=0.8, handlelength=2, handletextpad=1, fontsize=8, facecolor='white',
               markerscale=0.8, frameon=False, edgecolor='none', ncol=4)  # Ajuste de las columnas de la leyenda
    # Ajustar el tamaño y la posición de la leyenda
    plt.subplots_adjust(right=0.8)
    # Guardar la gráfica como una imagen en memoria
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    # Codificar la imagen en base64
    imagen_base64 = base64.b64encode(buffer.read()).decode()
    return imagen_base64

def obtener_moda(datosConsultados, campo):
    moda = mode(datosConsultados[campo])
    return moda

def calcular_frecuencia(datosConsultados, campo):
    frecuencia = datosConsultados[campo].value_counts()
    return frecuencia


def calcular_porcentaje(datosConsultados, campo):
    conteo = datosConsultados[campo].str.lower().value_counts()  # Convertir a minúsculas
    porcentaje = conteo / len(datosConsultados) * 100
    return porcentaje

def obtener_promedio_edad(datosConsultados):
    promedio = datosConsultados['edad'].astype(float).mean()
    promedio = int(promedio)
    return promedio

#esta funcion desenpaqueta los datos extraidos de la nube y retorna los datos con los filtros especificados
def bajar_datos(limite_datos,departamento):
    if departamento == "NACIONAL":
        results = client.get("gt2j-8ykr", limit=limite_datos)
    else:
        results = client.get("gt2j-8ykr",limit = limite_datos,departamento_nom = departamento)
    results_df = pd.DataFrame.from_records(results)
    return results_df


def home(request):
    if request.method == 'POST':
        departamento = request.POST.get('departamentoIngresado')
        departamento = departamento.upper()
        numero_registros = request.POST.get('numeroRegistrosIngresados')
        # Aquí puedes realizar cualquier lógica adicional con los datos recibidos

        print(f'{departamento}, {numero_registros}')
        # Por ejemplo, puedes renderizar una nueva plantilla y pasar los datos como contexto
        return HttpResponseRedirect(reverse('resultados', args=(departamento, numero_registros)))

    return render(request, 'ingresarDatos.html')

def resultados(request, departamento, numero_registros):

    #columnas_a_flitrar = ['ciudad_municipio_nom', 'departamento_nom', 'edad', 'fuente_tipo_contagio', 'estado']
    datosConsultados = bajar_datos(numero_registros,departamento)
    #print(datosConsultados)
    promedioEdad = obtener_promedio_edad(datosConsultados)
    frecuenciaEdad =  calcular_frecuencia(datosConsultados,'edad')
    graficaEdad = graficaLineaFrecuencia(frecuenciaEdad)
    modaFuenteTipoContagio = obtener_moda(datosConsultados,'fuente_tipo_contagio')
    porcentajeFuenteTipoContagio = calcular_porcentaje(datosConsultados, 'fuente_tipo_contagio')
    porcentajeTipoRecuperacion = calcular_porcentaje(datosConsultados, 'tipo_recuperacion')
    porcentajeSexo = calcular_porcentaje(datosConsultados,'sexo')
    porcentajeEstado = calcular_porcentaje(datosConsultados,'estado')
    porcentajeUbicacionCaso = calcular_porcentaje(datosConsultados,'ubicacion')
    frecuenciaGrupo = calcular_frecuencia(datosConsultados,'nom_grupo_')
    graficaGrupo = graficaAnilloFrecuencia(frecuenciaGrupo, 'Frecuencia de Grupos etnicos', 'Grupos etnicos')
    frecuenciaMunicipios = calcular_frecuencia(datosConsultados,'ciudad_municipio_nom')
    graficaMunicipios = graficaAnilloFrecuencia(frecuenciaMunicipios, 'Frecuencia de municipios', 'Municipios')


    datos = {'departamento': departamento, 'numero_registros': numero_registros, 'promedioEdad': promedioEdad,\
             'modaFuenteTipoContagio':modaFuenteTipoContagio,'porcentajeFuenteTipoContagio': porcentajeFuenteTipoContagio,\
             'porcentajeSexo': porcentajeSexo,'graficaMunicipios': graficaMunicipios, 'porcentajeTipoRecuperacion':porcentajeTipoRecuperacion,\
             'porcentajeEstado':porcentajeEstado,'porcentajeUbicacionCaso':porcentajeUbicacionCaso,'frecuenciaGrupo':frecuenciaGrupo,\
             'graficaGrupo': graficaGrupo,'graficaEdad':graficaEdad}
    return render(request, 'resultados.html', datos)