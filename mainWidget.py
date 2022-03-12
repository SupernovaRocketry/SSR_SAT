from kivy.uix.behaviors import button
import kivy
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
# from kivy.uix.image import AsyncImage
from kivy.core.window import Window
from kivy.graphics.svg import Svg
from popups import ConnectSocketPopup
from timeseriesgraph import TimeSeriesGraph
from kivy_garden.graph import LinePlot
from cliente import Cliente
from threading import Thread
from time import sleep

class MainWidget(FloatLayout):
    '''
    Widget principal do supervisório
    '''
    _updateWidgets = True
    _max_points = 1000
    _supernova_color = "#7D0101"
    _color_graphs = (1,0,0)
    _color_graphs_y = (0,1,0)
    _color_graphs_z = (0,0,1)

    def __init__(self, **kwargs):
        '''
        Construtor do widget principal
        '''
        super().__init__()
        self._login = ""
        self._senha = ""
        self._missao = ""
        self._apogeu = 1
        self._serverIP = kwargs.get('server_ip')
        self._port = kwargs.get('server_port')
        self._conn = ConnectSocketPopup(self._serverIP, self._port)
        
        
        #self._connect.start()
        Window.fullscreen = False
        Window.maximize()

        
        self._graphAltitude = self.DataGraph(self._max_points, self._color_graphs)
        self._graphAcelerometro = self.DataGraphAcel(self._max_points, self._color_graphs, self._color_graphs_y, self._color_graphs_z)
        self._graphGiroscopio = self.DataGraphGiro(self._max_points, self._color_graphs, self._color_graphs_y, self._color_graphs_z)
    pass

    def startDataRead(self, ip, port):
        """
        Método utilizado para configurar a conexão socket e inicializar uma thread para a leitura dos dados e atualização da interface grafica
        :param ip: ip da conexão socket
        :param port: porta para a conexao socket
        """
        self._serverIP = ip
        self._serverPort = port
        if self._login == 'supernova' and self._senha == 'astra':
            try:
                Window.set_system_cursor("wait")
                self._connect = Cliente(self._serverIP, self._port)
                self._connect.start()
                Window.set_system_cursor("arrow")
                self._updateThread = Thread(target = self.updater)
                self._updateThread.start()
                self.ids.imagem_conexao.background_normal = 'imgs/conectado.png'
                self._limitesGraficos()
                self._conn.dismiss()
            except:
                print("Falha ao inicinar startDataRead")
        else:
            print("Senha invalida!")

    
    def updater(self):
        """
        Metodo que invoca as rotinas de leitura de dados, utilizando a interface e inserção dos dados no banco de dados
        """
        try:
            while self._updateWidgets:
                #ler dados
                #atualizar a interface
                #insedir os dados no banco de dados

                #Le dados
                self.readData()

                # Atualiza dados
                self._updateGUI()


                #sleep(.05)
        except Exception as e:
            print(f'Erro: {e}')

    
    def readData(self):
        """
        Método para a leitura de dados via socket
        """
        try:
            self._instDados = self._connect._method()
        except Exception as e:
            print(f'Falha ao adquirir os dados: {e}')

    def _updateGUI(self):
        """
        Método para a atualização dos da interface gráfica
        """
        self.ids.altitude.text = str(self._instDados['Altitude'])
        self.ids.latitude.text = str(self._instDados['Latitude'])
        self.ids.longitude.text = str(self._instDados['Longitude'])
        self.ids.acelerometroX.text = str("{:.2f}".format(self._instDados['Acelerometro']['x']))
        self.ids.acelerometroY.text = str("{:.2f}".format(self._instDados['Acelerometro']['y']))
        self.ids.acelerometroZ.text = str("{:.1f}".format(self._instDados['Acelerometro']['z']))
        self.ids.giroscopioX.text = str(int(self._instDados['Giroscopio']['x']))
        self.ids.giroscopioY.text = str(int(self._instDados['Giroscopio']['y']))
        self.ids.giroscopioZ.text = str(int(self._instDados['Giroscopio']['z']))
        self.ids.RSSI.text = str(self._instDados['RSSI'])
        self.ids.mapa.lat = self._instDados['Latitude']
        self.ids.mapa.lon = self._instDados['Longitude']


        self.updateBoolean()
                                                   
        # Atualiza o grafico vertical de altitude
        self.ids.graficoMedidorAltitude.size_hint = (self.ids.medidorAltitude.size_hint[0], float(self._instDados['Altitude']/(1.2*self._apogeu))*self.ids.medidorAltitude.size_hint[1]) if self._instDados['Altitude'] <= 1.2*self._apogeu else (self.ids.medidorAltitude.size_hint[0], self.ids.medidorAltitude.size_hint[1])
        # self.ids.linhaGraficoMedidorAltitude.pos = (self.ids.medidorAltitude.pos[0], self.ids.medidorAltitude.pos[1] + float(self._instDados['Altitude']/36)*self.ids.medidorAltitude.size_hint[1])

        #Atualiza o grafico de linhas de altitude
        self.ids.graphAltitude.updateGraph((self._instDados['timestamp'], self._instDados['Altitude']),0)

        # Atualiza o grafico com dados do acelerometro
        self.ids.graphAcelerometro.updateGraph((self._instDados['timestamp'], self._instDados['Acelerometro']['x']), 0)
        self.ids.graphAcelerometro.updateGraph((self._instDados['timestamp'], self._instDados['Acelerometro']['y']), 1)
        self.ids.graphAcelerometro.updateGraph((self._instDados['timestamp'], self._instDados['Acelerometro']['z']), 2)
        
        # # Atualiza o grafico com dados do giroscopio
        self.ids.graphGiroscopio.updateGraph((self._instDados['timestamp'], self._instDados['Giroscopio']['x']), 0)
        self.ids.graphGiroscopio.updateGraph((self._instDados['timestamp'], self._instDados['Giroscopio']['y']), 1)
        self.ids.graphGiroscopio.updateGraph((self._instDados['timestamp'], self._instDados['Giroscopio']['z']), 2)

        

    
    def stopRefresh(self):
        self._updateWidgets = False


    def _limitesGraficos(self):
        self.ids.graphAltitude.ymax = self._apogeu*1.2
        self.ids.graphAltitude.y_ticks_major = self._apogeu*1.2/6
        if self._apogeu == 500:
            self.ids.escala.source = 'imgs/escala500.png'
        if self._apogeu == 1000:
            self.ids.escala.source = 'imgs/escala1000.png'
        if self._apogeu == 3000:
            self.ids.escala.source = 'imgs/escala3000.png'
        if self._apogeu == 5000:
            self.ids.escala.source = 'imgs/escala5000.png'

    def DataGraph(self, xmax, plot_color, **kwargs):
        # super().__init__(**kwargs)
        plot = LinePlot(line_width = 1.5, color = plot_color)
        self.ids.graphAltitude.add_plot(plot)
        self.ids.graphAltitude.xmax = xmax
            

    def DataGraphAcel(self, xmax, plot_color, plot_color_y, plot_color_z, **kwargs):
        plot = LinePlot(line_width = 1.5, color = plot_color)
        plot2 = LinePlot(line_width = 1.5, color = plot_color_y)
        plot3 = LinePlot(line_width = 1.5, color = plot_color_z)
        self.ids.graphAcelerometro.add_plot(plot)
        self.ids.graphAcelerometro.add_plot(plot2)
        self.ids.graphAcelerometro.add_plot(plot3)        
        self.ids.graphAcelerometro.xmax = xmax

    def DataGraphGiro(self, xmax, plot_color, plot_color_y, plot_color_z, **kwargs):
        plot = LinePlot(line_width = 1.5, color = plot_color)
        plot2 = LinePlot(line_width = 1.5, color = plot_color_y)
        plot3 = LinePlot(line_width = 1.5, color = plot_color_z)
        self.ids.graphGiroscopio.add_plot(plot)
        self.ids.graphGiroscopio.add_plot(plot2)
        self.ids.graphGiroscopio.add_plot(plot3)
        self.ids.graphGiroscopio.xmax = xmax
        


    def updateBoolean(self):
        if self._instDados['Principal Paraquedas Estabilizador'] == 1:
            self.ids.paraquedasEstabilizadorPrincipal.source = 'imgs/green_led.png'
        
        if self._instDados['Redundancia Paraquedas Estabilizador'] == 1:
            self.ids.paraquedasEstabilizadorRedundante.source = 'imgs/green_led.png'

        if self._instDados['Comercial Paraquedas Estabilizador'] == 1:
            self.ids.paraquedasEstabilizadorComercial.source = 'imgs/green_led.png'

        if self._instDados['Principal Paraquedas Principal'] == 1:
            self.ids.paraquedasPrincipal.source = 'imgs/green_led.png'

        if self._instDados['Comercial Paraquedas Principal'] == 1:
            self.ids.paraquedasPrincipalComercial.source = 'imgs/green_led.png'
# class DataGraph(FloatLayout):    
#     def __init__ (self, xmax, plot_color, **kwargs):
        