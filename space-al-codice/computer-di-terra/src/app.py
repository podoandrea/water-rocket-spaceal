"""
app.py
------
Dashboard "SPACE AL" per il monitoraggio in tempo reale di un lancio
(razzo/payload con paracadute): altitudine, assetto (pitch/roll) e
stato del paracadute, con cronometro di volo e storico dei lanci.

Punto di ingresso dell'applicazione. Esegui con:
    python src/app.py

La sorgente dei dati (radio nRF24L01 su Raspberry Pi oppure seriale
USB) si seleziona tramite config.MODALITA_INPUT (vedi config.py o
variabile d'ambiente SPACEAL_INPUT_MODE).
"""

import dash
import plotly.graph_objs as go
from dash import Dash, dcc, html, Output, Input

import config
from gpio_compat import get_gpio
from state import FlightState, avvia_thread_cronometro

GPIO = get_gpio()

# ---------------------------------------------------------------------
# Inizializzazione GPIO (pulsanti fisici, usati in entrambe le modalita'
# quando disponibili; su piattaforme non Raspberry restano sempre "alti")
# ---------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.PIN_AVVIA, GPIO.IN)
GPIO.setup(config.PIN_PAUSA, GPIO.IN)
GPIO.setup(config.PIN_RESET, GPIO.IN)
GPIO.setup(config.PIN_REFRESH, GPIO.IN)

# ---------------------------------------------------------------------
# Inizializzazione sorgente dati
# ---------------------------------------------------------------------
reader = None
if config.MODALITA_INPUT == "radio":
    from radio_reader import RadioReader
    reader = RadioReader(
        ce_pin=config.RADIO_CE_PIN,
        csn_pin=config.RADIO_CSN_PIN,
        channel=config.RADIO_CHANNEL,
        payload_size=config.RADIO_PAYLOAD_SIZE,
        pipe_address=config.RADIO_PIPE_ADDRESS,
    )
    print("Modalita' radio (nRF24L01) attiva. In ascolto...")
elif config.MODALITA_INPUT == "serial":
    from serial_reader import SerialReader
    reader = SerialReader(
        port=config.SERIAL_PORT,
        baudrate=config.SERIAL_BAUDRATE,
        timeout=config.SERIAL_TIMEOUT,
    )
    print(f"Modalita' seriale attiva su {config.SERIAL_PORT}.")
else:
    raise ValueError(
        f"MODALITA_INPUT non valida: '{config.MODALITA_INPUT}'. "
        "Valori ammessi: 'radio', 'serial'."
    )

# ---------------------------------------------------------------------
# Stato condiviso e thread del cronometro
# ---------------------------------------------------------------------
state = FlightState()
avvia_thread_cronometro(state)

app = Dash(__name__)
app.title = "SPACE AL - Telemetria di volo"


def _stile_immagine_paracadute(aperto: bool) -> dict:
    colore_glow = "lime" if aperto else "red"
    return {
        "width": "50px",
        "padding": "10px",
        "borderRadius": "10px",
        "boxShadow": f"0px 0px {'40' if aperto else '20'}px {colore_glow}",
        "transition": "box-shadow 0.3s ease-in-out",
        "position": "absolute",
        "bottom": "30px",
        "left": "30px",
    }


# ---------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------
app.layout = html.Div(
    [
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "flex-start",
                "height": "400px",
            },
            children=[
                html.Div(
                    style={"width": "50%", "height": "100%", "position": "relative"},
                    children=[
                        dcc.Graph(
                            id="grafico-dinamico",
                            style={"width": "100%", "height": "100%"},
                            config={"displayModeBar": False},
                            figure={
                                "layout": {
                                    "template": "plotly_dark",
                                    "plot_bgcolor": "#1e1e1e",
                                    "paper_bgcolor": "#121212",
                                    "font": {"color": "#FFF"},
                                }
                            },
                        ),
                        dcc.Checklist(
                            id="checklist-grafici",
                            options=[],
                            value=[],
                            inline=True,
                            style={
                                "position": "absolute",
                                "right": "10px",
                                "top": "10px",
                                "display": "none",
                            },
                        ),
                    ],
                )
            ],
        ),
        html.Div(
            html.H1(
                "SPACE AL",
                style={
                    "font-family": "Orbitron",
                    "font-style": "oblique",
                    "text-align": "center",
                    "line-height": "150px",
                },
            ),
            style={"background-color": "#d2d2d2", "height": "5vh", "width": "99vw"},
        ),
        dcc.Interval(
            id="interval-component",
            interval=config.INTERVALLO_LETTURA_MS,
            n_intervals=0,
        ),
        html.Div(
            style={
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
                "marginTop": "20px",
                "color": "white",
                "position": "relative",
            },
            children=[
                html.H1("Cronometro", style={"fontFamily": "Orbitron"}),
                html.H3(id="display-tempo", children="0.0 secondi"),
                html.Div(
                    [
                        html.Button(
                            "Avvia",
                            id="avvia",
                            n_clicks=0,
                            style={
                                "padding": "10px 20px",
                                "marginBottom": "10px",
                                "borderRadius": "1000px",
                                "border": "2px solid white",
                                "backgroundColor": "black",
                                "color": "white",
                            },
                        ),
                        html.Button(
                            "Pausa",
                            id="pausa",
                            n_clicks=0,
                            style={
                                "padding": "10px 20px",
                                "marginBottom": "10px",
                                "borderRadius": "1000px",
                                "border": "2px solid white",
                                "backgroundColor": "black",
                                "color": "white",
                            },
                        ),
                        html.Button(
                            "Reset",
                            id="reset",
                            n_clicks=0,
                            style={
                                "padding": "10px 20px",
                                "marginBottom": "10px",
                                "borderRadius": "1000px",
                                "border": "2px solid white",
                                "backgroundColor": "black",
                                "color": "white",
                            },
                        ),
                        html.Button(
                            "Refresh",
                            id="refresh",
                            n_clicks=0,
                            style={
                                "padding": "10px 20px",
                                "marginBottom": "10px",
                                "borderRadius": "1000px",
                                "border": "2px solid white",
                                "backgroundColor": "black",
                                "color": "white",
                            },
                        ),
                    ],
                    style={"display": "flex", "gap": "10px", "marginTop": "10px"},
                ),
                html.Img(
                    id="image",
                    src=config.IMMAGINE_PARACADUTE_URL,
                    style=_stile_immagine_paracadute(False),
                ),
            ],
        ),
        dcc.Store(id="store-coordinate", data={"x": 0, "y": 0, "alt": 0}),
        dcc.Interval(
            id="intervallo-grafico",
            interval=config.INTERVALLO_GRAFICO_MS,
            n_intervals=0,
            disabled=True,
        ),
        dcc.Interval(
            id="intervallo-timer",
            interval=config.INTERVALLO_TIMER_MS,
            n_intervals=0,
            disabled=True,
        ),
        dcc.Store(id="reset-grafico", data=False),
    ],
    style={"background-color": "#111111", "height": "97.5vh", "width": "99vw"},
)


# ---------------------------------------------------------------------
# Callback: lettura dati dalla sorgente (radio o seriale)
# ---------------------------------------------------------------------
@app.callback(
    [Output("image", "style"), Output("store-coordinate", "data")],
    Input("interval-component", "n_intervals"),
)
def leggi_dati(_n_intervals):
    try:
        dati = reader.leggi_coordinate()
    except (TimeoutError, OSError) as e:
        print(f"Errore di lettura dalla sorgente dati: {e}")
        dati = None

    if dati is None:
        return _stile_immagine_paracadute(state.stato_paracadute), {
            "x": 0,
            "y": 0,
            "alt": 0,
        }

    if dati.get("paracadute_aperto"):
        state.imposta_paracadute_aperto()

    coordinate = {"x": dati["x"], "y": dati["y"], "alt": dati["alt"]}
    return _stile_immagine_paracadute(state.stato_paracadute), coordinate


# ---------------------------------------------------------------------
# Callback: aggiornamento testo cronometro
# ---------------------------------------------------------------------
@app.callback(
    Output("display-tempo", "children"),
    [Input("intervallo-timer", "n_intervals"), Input("reset-grafico", "data")],
)
def aggiorna_display(_n_intervals, _reset):
    return f"{state.tempo:.1f} secondi"


# ---------------------------------------------------------------------
# Callback: gestione pulsanti (Avvia / Pausa / Reset / Refresh)
# ---------------------------------------------------------------------
def _opzioni_checklist():
    storico_grafici, storico_tempi = state.snapshot_storico()
    opzioni = [
        {"label": f"Lancio {i + 1} ({storico_tempi[i][1]:.1f}s)", "value": i}
        for i in range(len(storico_grafici))
    ]
    valori = list(range(len(storico_grafici)))
    return opzioni, valori


@app.callback(
    [
        Output("intervallo-timer", "disabled"),
        Output("intervallo-grafico", "disabled"),
        Output("reset-grafico", "data"),
        Output("checklist-grafici", "options"),
        Output("checklist-grafici", "value"),
    ],
    [
        Input("avvia", "n_clicks"),
        Input("pausa", "n_clicks"),
        Input("reset", "n_clicks"),
        Input("refresh", "n_clicks"),
    ],
)
def gestisci_pulsanti(_avvia, _pausa, _reset, _refresh):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

    # I pulsanti fisici GPIO hanno priorita' sui pulsanti software,
    # replicando il comportamento del prototipo hardware originale.
    if GPIO.input(config.PIN_AVVIA) == GPIO.LOW or trigger_id == "avvia":
        state.avvia()
        opzioni, valori = _opzioni_checklist()
        return False, False, False, opzioni, valori

    if GPIO.input(config.PIN_PAUSA) == GPIO.LOW or trigger_id == "pausa":
        state.pausa()
        opzioni, valori = _opzioni_checklist()
        return True, True, False, opzioni, valori

    if GPIO.input(config.PIN_RESET) == GPIO.LOW or trigger_id == "reset":
        state.reset()
        opzioni, valori = _opzioni_checklist()
        return True, True, True, opzioni, valori

    if GPIO.input(config.PIN_REFRESH) == GPIO.LOW or trigger_id == "refresh":
        print("Refresh richiesto")

    return (
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )


# ---------------------------------------------------------------------
# Callback: aggiornamento grafico altitudine
# ---------------------------------------------------------------------
@app.callback(
    Output("grafico-dinamico", "figure"),
    [
        Input("store-coordinate", "data"),
        Input("intervallo-grafico", "n_intervals"),
        Input("reset-grafico", "data"),
        Input("checklist-grafici", "value"),
    ],
)
def aggiorna_grafico(dati_coordinate, _n, reset_attivo, grafici_selezionati):
    figura = go.Figure()
    storico_grafici, storico_tempi = state.snapshot_storico()

    if reset_attivo:
        for i in grafici_selezionati:
            if i >= len(storico_grafici):
                continue
            x_data, y_data = storico_grafici[i]
            figura.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode="lines+markers",
                    name=f"Lancio {i + 1} ({storico_tempi[i][1]:.1f}s)",
                )
            )

    if state.in_esecuzione and dati_coordinate:
        state.aggiungi_punto(dati_coordinate.get("y", 0))

    asse_x, asse_y = state.snapshot_corrente()
    figura.add_trace(
        go.Scatter(x=asse_x, y=asse_y, mode="lines+markers", name="Dati in tempo reale")
    )

    figura.update_layout(
        template="plotly_dark",
        title="Altitudine",
        xaxis_title="Tempo (s)",
        yaxis_title="Altitudine (m)",
    )

    return figura


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

