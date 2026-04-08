import pandas as pd

def timeseries_fixture():
    dates = pd.date_range(end=pd.Timestamp("2026-04-07"), periods=12, freq="M")
    values = [72, 74, 73, 75, 77, 78, 80, 79, 81, 82, 83, 85]
    return pd.DataFrame({"date": dates, "value": values})

def semaforo_fixture():
    return pd.DataFrame({
        "estado": ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento"],
        "valor": [20, 24, 85, 115]
    })
