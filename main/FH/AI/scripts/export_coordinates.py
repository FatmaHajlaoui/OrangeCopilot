"""One-off script: export IP/Name -> coordinates from the RSL_Level table
so the AI pipeline can use real coordinates without re-parsing Excel files."""
import sys
from pathlib import Path

# make "main" importable — adjust if this script sits elsewhere
sys.path.append(str(Path(__file__).resolve().parents[4]))

from main import create_app
from main.FH.services.rsl_service import RSLLevelService

app = create_app()

with app.app_context():
    df = RSLLevelService.get_data()  # most recent upload
    if df is None:
        print("No RSL data found in the database.")
    else:
        coord_cols = ["IP", "Name", "EndA_Name", "EndA_Latitude", "EndA_Longitude",
                      "EndB_Name", "EndB_Latitude", "EndB_Longitude"]
        df_coords = df[coord_cols].drop_duplicates()
        output_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "link_coordinates.csv"
        df_coords.to_csv(output_path, index=False)
        print("Exported", len(df_coords), "rows to", output_path)