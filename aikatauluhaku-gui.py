import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
import requests
import json
from datetime import datetime

class AikatauluHakuGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Aikatauluhaku')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Lähtöpaikka
        lahto_layout = QHBoxLayout()
        lahto_layout.addWidget(QLabel('Lähtöpaikka:'))
        self.lahto_entry = QLineEdit()
        lahto_layout.addWidget(self.lahto_entry)
        layout.addLayout(lahto_layout)

        # Kohdepaikka
        kohde_layout = QHBoxLayout()
        kohde_layout.addWidget(QLabel('Kohdepaikka:'))
        self.kohde_entry = QLineEdit()
        kohde_layout.addWidget(self.kohde_entry)
        layout.addLayout(kohde_layout)

        # Haku-nappi
        self.haku_button = QPushButton('Hae aikataulut')
        self.haku_button.clicked.connect(self.hae_aikataulut)
        layout.addWidget(self.haku_button)

        # Päivitetään taulukon sarakkeet
        self.tulos_table = QTableWidget()
        self.tulos_table.setColumnCount(13)  # Lisätään yksi sarake päivämäärälle
        self.tulos_table.setHorizontalHeaderLabels([
            "Päivämäärä", "Lähtöaika", "Saapumisaika", "Kesto", "Hinta", "Yhtiö", "Linja",
            "Vuorotyyppi", "Nimi", "Ajopäivät", "Voimassa", "Pituus (km)", "Palvelut"
        ])
        self.tulos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tulos_table)

        self.setLayout(layout)

    def hae_aikataulut(self):
        lahto = self.lahto_entry.text()
        kohde = self.kohde_entry.text()
        
        url = "https://minfoapi.matkahuolto.fi/mlippu_rest/connections"
        
        params = {
            "departureStopAreaName": lahto,
            "arrivalStopAreaName": kohde,
            "allSchedules": 0,
            "departureDate": datetime.now().strftime("%Y-%m-%d"),
            "ticketTravelType": 0
        }
        
        headers = {
            "Accept": "application/vnd.matkahuolto.minfo.api-v1+json",
            "Authorization": "Basic VWxrQVBJQXZvaW46QlVzMjhEZWZ1TmFiPzhhajNwM2VxZWdh",
            "Accept-Language": "fi"
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            self.nayta_aikataulut(data)
        except requests.exceptions.RequestException as e:
            self.tulos_table.setRowCount(1)
            self.tulos_table.setSpan(0, 0, 1, 13)  # Päivitetään span kattamaan uusi sarake
            self.tulos_table.setItem(0, 0, QTableWidgetItem(f"Virhe haussa: {str(e)}"))

    def nayta_aikataulut(self, data):
        self.tulos_table.setRowCount(0)
        
        if 'connections' not in data or len(data['connections']) == 0:
            self.tulos_table.setRowCount(1)
            self.tulos_table.setSpan(0, 0, 1, 13)  # Päivitetään span kattamaan uusi sarake
            self.tulos_table.setItem(0, 0, QTableWidgetItem("Ei löytynyt yhteyksiä annetuilla hakuehdoilla."))
            return
        
        for connection in data['connections']:
            row_position = self.tulos_table.rowCount()
            self.tulos_table.insertRow(row_position)
            
            lahtoaika_str = connection['fromPlace']['dateTime']
            saapumisaika_str = connection['toPlace']['dateTime']
            
            # Käytetään datetime.fromisoformat() -funktiota ISO 8601 -muotoisen ajan jäsentämiseen
            lahtoaika = datetime.fromisoformat(lahtoaika_str)
            saapumisaika = datetime.fromisoformat(saapumisaika_str)
            
            paivamaara = lahtoaika.strftime("%Y-%m-%d")
            lahtoaika_kello = lahtoaika.strftime("%H:%M")
            saapumisaika_kello = saapumisaika.strftime("%H:%M")
            
            kesto = connection['duration']
            hinta = connection.get('adultPrice', 'N/A')
            yhtio = connection['companies'][0]['name'] if connection['companies'] else 'N/A'
            linja = connection['line'].get('number', 'N/A')
            vuorotyyppi = connection['line'].get('departureType', 'N/A')
            nimi = connection['line'].get('name', 'N/A')
            ajopaivat = connection['line'].get('daysOfOperationLong', 'N/A')
            voimassa = connection['line'].get('validityPeriod', 'N/A')
            pituus = connection['line'].get('lengthKm', 'N/A')
            palvelut = ', '.join([service.get('service', '') for service in connection['line'].get('services', [])])
            
            self.tulos_table.setItem(row_position, 0, QTableWidgetItem(paivamaara))
            self.tulos_table.setItem(row_position, 1, QTableWidgetItem(lahtoaika_kello))
            self.tulos_table.setItem(row_position, 2, QTableWidgetItem(saapumisaika_kello))
            self.tulos_table.setItem(row_position, 3, QTableWidgetItem(str(kesto)))
            self.tulos_table.setItem(row_position, 4, QTableWidgetItem(f"{hinta}€" if hinta != 'N/A' else 'N/A'))
            self.tulos_table.setItem(row_position, 5, QTableWidgetItem(str(yhtio)))
            self.tulos_table.setItem(row_position, 6, QTableWidgetItem(str(linja)))
            self.tulos_table.setItem(row_position, 7, QTableWidgetItem(str(vuorotyyppi)))
            self.tulos_table.setItem(row_position, 8, QTableWidgetItem(str(nimi)))
            self.tulos_table.setItem(row_position, 9, QTableWidgetItem(str(ajopaivat)))
            self.tulos_table.setItem(row_position, 10, QTableWidgetItem(str(voimassa)))
            self.tulos_table.setItem(row_position, 11, QTableWidgetItem(str(pituus)))
            self.tulos_table.setItem(row_position, 12, QTableWidgetItem(palvelut))

        self.tulos_table.resizeColumnsToContents()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AikatauluHakuGUI()
    ex.show()
    sys.exit(app.exec_())