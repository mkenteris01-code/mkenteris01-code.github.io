"""
Codebook Compliance Check
Compares extracted CSV against DOC_Data_Extraction_Codebook_v1.0.pdf requirements
"""
import pandas as pd

df = pd.read_csv('Data_Extraction_Results_v1.csv')

print("="*70)
print("CODEBOOK COMPLIANCE CHECK")
print("="*70)

# Expected columns from codebook
codebook_required = {
    "Basic Info": ["study_id", "author", "year", "title"],
    "LLM Variables": ["llm_model_name", "parameter_count", "slm_feasibility"],
    "FL Variables": ["FL_Strategy", "PEFT_Method"],  # ⚠️ FL_Strategy vs fl_architecture
    "Privacy": ["privacy_mechanism"],
    "KG Variables": ["kg_type", "Grounding_Dimension_1", "Grounding_Dimension_2"],
    "Pedagogical": ["cefr_alignment", "Skill_Focus"],  # ⚠️ Skill_Focus missing?
    "Metrics": ["validation_metrics"],
    "Quality": ["confidence_score", "extraction_notes"]
}

# Actual columns in our CSV
actual_columns = df.columns.tolist()

print("\n1. COLUMN MAPPING CHECK")
print("-" * 70)

all_required = []
for category, cols in codebook_required.items():
    all_required.extend(cols)

missing_cols = []
renamed_cols = []

for req_col in all_required:
    if req_col not in actual_columns:
        # Check if it's renamed
        if req_col == "FL_Strategy" and "fl_architecture" in actual_columns:
            renamed_cols.append(f"'{req_col}' -> 'fl_architecture' (RENAMED)")
        elif req_col == "Grounding_Dimension_1" and "control_gap_addressed" in actual_columns:
            renamed_cols.append(f"'{req_col}' -> 'control_gap_addressed' (DIFFERENT FORMAT)")
        elif req_col == "Grounding_Dimension_2" and "grounding_gap_addressed" in actual_columns:
            renamed_cols.append(f"'{req_col}' -> 'grounding_gap_addressed' (DIFFERENT FORMAT)")
        else:
            missing_cols.append(req_col)

if missing_cols:
    print("[X] MISSING COLUMNS:")
    for col in missing_cols:
        print(f"   - {col}")
else:
    print("[OK] All required columns present")

if renamed_cols:
    print("\n[!] RENAMED/DIFFERENT COLUMNS:")
    for col in renamed_cols:
        print(f"   - {col}")

print("\n2. VALUE COMPLIANCE CHECK")
print("-" * 70)

# Check FL_Strategy values
print("\n>> FL_Strategy (codebook wants: FedAvg, FedPer/FedRep, P2P):")
fl_values = df['fl_architecture'].unique()
print(f"   Actual values: {fl_values}")
if any(v in ['Centralized', 'Decentralized'] for v in fl_values if v != 'NR'):
    print("   [!] WARNING: Using 'Centralized/Decentralized' instead of specific strategies")

# Check PEFT_Method
if 'PEFT_Method' in actual_columns:
    peft_values = df['PEFT_Method'].unique()
    print(f"\n>> PEFT_Method: {peft_values}")
else:
    print("\n>> PEFT_Method: [X] NOT EXTRACTED")

# Check KG_Type values
print("\n>> KG_Type (codebook wants: Ontology, Property Graph, ConceptNet):")
kg_values = df['kg_type'].unique()
print(f"   Actual values: {kg_values}")
if 'RAG' in kg_values:
    print("   [!] WARNING: 'RAG' found but not in codebook enum")
if 'Property Graph' not in kg_values:
    print("   [i] INFO: 'Property Graph' not found in any papers")

# Check Grounding Dimensions
print("\n>> Grounding Dimensions (codebook wants: binary 0/1):")
if 'Grounding_Dimension_1' in actual_columns:
    gd1_values = df['Grounding_Dimension_1'].unique()
    print(f"   Grounding_Dimension_1: {gd1_values}")
else:
    print("   Grounding_Dimension_1: [X] NOT EXTRACTED")
    print(f"   Instead using: control_gap_addressed = {df['control_gap_addressed'].unique()}")
    print("   [!] WARNING: Using Yes/No/Partial instead of 0/1")

if 'Grounding_Dimension_2' in actual_columns:
    gd2_values = df['Grounding_Dimension_2'].unique()
    print(f"   Grounding_Dimension_2: {gd2_values}")
else:
    print("   Grounding_Dimension_2: [X] NOT EXTRACTED")
    print(f"   Instead using: grounding_gap_addressed = {df['grounding_gap_addressed'].unique()}")
    print("   [!] WARNING: Using Yes/No/Partial instead of 0/1")

# Check Skill_Focus
print("\n>> Skill_Focus (codebook wants: Productive, Receptive, Systemic):")
if 'Skill_Focus' in actual_columns:
    skill_values = df['Skill_Focus'].unique()
    print(f"   Values: {skill_values}")
else:
    print("   [X] NOT EXTRACTED")

# Check Validation_Metrics
print("\n>> Validation_Metrics (codebook wants: KGQI, ACI, HITL):")
val_values = df['validation_metrics'].unique()
print(f"   Actual values: {val_values}")
compliant_vals = ['KGQI', 'ACI', 'HITL', 'NR']
non_compliant = [v for v in val_values if v not in compliant_vals]
if non_compliant:
    print(f"   [!] WARNING: Non-codebook values: {non_compliant}")

# Check CEFR
print("\n>> CEFR_Alignment (codebook wants: A1-C2 or Beginner/Intermediate/Advanced):")
cefr_values = df['cefr_alignment'].unique()
print(f"   Actual values: {cefr_values}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

critical_gaps = []
if 'PEFT_Method' not in actual_columns:
    critical_gaps.append("PEFT_Method (LoRA/QLoRA/Full FT)")
if 'Skill_Focus' not in actual_columns:
    critical_gaps.append("Skill_Focus (Productive/Receptive/Systemic)")
if 'Grounding_Dimension_1' not in actual_columns:
    critical_gaps.append("Grounding_Dimension_1 (binary 0/1 for symbolic control)")
if 'Grounding_Dimension_2' not in actual_columns:
    critical_gaps.append("Grounding_Dimension_2 (binary 0/1 for source verification)")

if critical_gaps:
    print("\n[X] CRITICAL GAPS - These variables are REQUIRED by codebook:")
    for gap in critical_gaps:
        print(f"   - {gap}")
    print("\n[!] RECOMMENDATION: Update extraction code to include these fields")
else:
    print("\n[OK] All critical variables extracted!")

print("\n[OSF READINESS]:")
if len(critical_gaps) > 0:
    print("   [!] PARTIAL - You have most data, but missing", len(critical_gaps), "codebook variables")
    print("   [!] Consider re-running extraction with updated prompts, OR")
    print("   [OK] Document the deviation in your OSF methodology notes")
else:
    print("   [OK] READY - All codebook requirements met")
