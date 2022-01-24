import gfdlvitals
from dora.scalar import gfdlvitals_plot

def test_scalar_figure_generation():
    df_hist = gfdlvitals.open_db(gfdlvitals.sample.historical)
    uri = gfdlvitals_plot(df_hist,"t_ref")
