import sys
print(sys.executable)
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit
from PyQt5.QtCore import Qt, QDate
from urllib import request, parse
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from PyQt5.QtGui import QColor

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
        
        # Päivämäärävalinta
        pvm_layout = QHBoxLayout()
        pvm_layout.addWidget(QLabel('Päivämäärä:'))
        self.pvm_valinta = QDateEdit()
        self.pvm_valinta.setDate(QDate.currentDate())
        self.pvm_valinta.setCalendarPopup(True)
        pvm_layout.addWidget(self.pvm_valinta)
        pvm_layout.addStretch()  # Add this line
        layout.addLayout(pvm_layout)

        # Haku-nappi
        self.haku_button = QPushButton('Hae aikataulut')
        self.haku_button.clicked.connect(self.hae_aikataulut)
        layout.addWidget(self.haku_button)

        # Päivitetään taulukon sarakkeet
        self.tulos_table = QTableWidget()
        self.tulos_table.setColumnCount(14)  # Increase column count by 1
        self.tulos_table.setHorizontalHeaderLabels([
            "Päivämäärä", "Lähtöaika", "Saapumisaika", "Kesto", "Hinta", "Yhtiö", "Linja",
            "Vuorotyyppi", "Nimi", "Ajopäivät", "Voimassa", "Pituus (km)", "Palvelut", "Pysäkki"
        ])
        self.tulos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tulos_table)

        self.setLayout(layout)

    def hae_aikataulut(self):
        lahto = self.lahto_entry.text()
        kohde = self.kohde_entry.text()
        valittu_pvm = self.pvm_valinta.date().toPyDate()
        
        # Get current time
        now = datetime.now()
        
        # If selected date is today, use current time. Otherwise, use 00:00
        if valittu_pvm == now.date():
            lahtoaika = now.strftime("%H:%M")
        else:
            lahtoaika = "00:00"
        
        url = "https://minfoapi.matkahuolto.fi/mlippu_rest/connections"
        
        params = {
            "departureStopAreaName": lahto,
            "arrivalStopAreaName": kohde,
            "allSchedules": 0,
            "departureDate": valittu_pvm.strftime("%Y-%m-%d"),
            "departureTime": lahtoaika,
            "ticketTravelType": 0
        }
        
        headers = {
            "Accept": "application/vnd.matkahuolto.minfo.api-v1+json",
            "Authorization": "Basic VWxrQVBJQXZvaW46QlVzMjhEZWZ1TmFiPzhhajNwM2VxZWdh",
            "Accept-Language": "fi"
        }
        
        try:
            url_params = parse.urlencode(params)
            full_url = f"{url}?{url_params}"
            req = request.Request(full_url, headers=headers)
            with request.urlopen(req) as response:
                data = json.loads(response.read().decode())
            
            self.nayta_aikataulut(data)
        except Exception as e:
            self.tulos_table.setRowCount(1)
            self.tulos_table.setSpan(0, 0, 1, 14)
            self.tulos_table.setItem(0, 0, QTableWidgetItem(f"Virhe haussa: {str(e)}"))

    def nayta_aikataulut(self, data):
        self.tulos_table.setRowCount(0)
        
        if 'connections' not in data or len(data['connections']) == 0:
            self.tulos_table.setRowCount(1)
            self.tulos_table.setSpan(0, 0, 1, 14)
            self.tulos_table.setItem(0, 0, QTableWidgetItem("Ei löytynyt yhteyksiä annetuilla hakuehdoilla."))
            return
        
        # Use Finland's timezone
        finland_tz = ZoneInfo("Europe/Helsinki")
        now = datetime.now(finland_tz)
        
        for i, connection in enumerate(data['connections']):
            lahtoaika_str = connection['fromPlace']['dateTime']
            # Parse the ISO format string and set it to Finland's timezone without conversion
            lahtoaika = datetime.fromisoformat(lahtoaika_str).replace(tzinfo=finland_tz)
            
            # Skip past departures
            if lahtoaika <= now:
                continue
            
            row_position = self.tulos_table.rowCount()
            self.tulos_table.insertRow(row_position)
            
            # Set alternating row colors
            row_color = Qt.lightGray if i % 2 != 0 else Qt.white
            text_color = QColor(0, 0, 0)  # Black text for all rows
            
            saapumisaika_str = connection['toPlace']['dateTime']
            saapumisaika = datetime.fromisoformat(saapumisaika_str).replace(tzinfo=finland_tz)
            
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
            
            # Fetch the stop name
            pysakki = connection['fromPlace'].get('stopAreaName', 'N/A')
            
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
            self.tulos_table.setItem(row_position, 13, QTableWidgetItem(str(pysakki)))  # Add the new 'Pysäkki' column
            
            # Apply background color and text color to each cell in the row
            for col in range(self.tulos_table.columnCount()):
                item = self.tulos_table.item(row_position, col)
                if item:
                    item.setBackground(row_color)
                    item.setForeground(text_color)

        self.tulos_table.resizeColumnsToContents()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AikatauluHakuGUI()
    ex.show()
    sys.exit(app.exec_())