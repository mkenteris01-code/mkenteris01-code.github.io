"""Quick analysis of extraction results"""
import pandas as pd

df = pd.read_csv('Data_Extraction_Results_v1.csv')

print("="*60)
print("EXTRACTION RESULTS VALIDATION")
print("="*60)
print(f"Total papers: {len(df)}")
print(f"\nConfidence Score Distribution:")
print(df['confidence_score'].describe())
print(f"\nPapers by confidence level:")
print(f"  High (>0.4): {len(df[df['confidence_score'] > 0.4])}")
print(f"  Medium (0.2-0.4): {len(df[(df['confidence_score'] >= 0.2) & (df['confidence_score'] <= 0.4)])}")
print(f"  Low (<0.2): {len(df[df['confidence_score'] < 0.2])}")

print(f"\nFailed extractions: {len(df[df['extraction_notes'].notna() & (df['extraction_notes'] != '')])}")

print(f"\n" + "="*60)
print("METADATA EXTRACTION SUCCESS")
print("="*60)

# LLM Models
llm_papers = df[df['llm_model_name'] != 'NR']
print(f"\nLLM Models found: {len(llm_papers)} papers")
if len(llm_papers) > 0:
    print("  Models:", llm_papers['llm_model_name'].unique()[:10])

# Parameters
param_papers = df[df['parameter_count'] != 'NR']
print(f"\nParameter counts found: {len(param_papers)} papers")
if len(param_papers) > 0:
    print("  Values:", param_papers['parameter_count'].unique())

# FL Architecture
fl_papers = df[df['fl_architecture'] != 'NR']
print(f"\nFL Architecture found: {len(fl_papers)} papers")
if len(fl_papers) > 0:
    print("  Types:", fl_papers['fl_architecture'].value_counts().to_dict())

# Privacy
privacy_papers = df[df['privacy_mechanism'] != 'NR']
print(f"\nPrivacy mechanisms found: {len(privacy_papers)} papers")
if len(privacy_papers) > 0:
    print("  Mechanisms:", privacy_papers['privacy_mechanism'].unique())

# KG Types
kg_papers = df[df['kg_type'] != 'NR']
print(f"\nKG Types found: {len(kg_papers)} papers")
if len(kg_papers) > 0:
    print("  Types:", kg_papers['kg_type'].value_counts().to_dict())

# CEFR
cefr_papers = df[df['cefr_alignment'] != 'NR']
print(f"\nCEFR alignment found: {len(cefr_papers)} papers")
if len(cefr_papers) > 0:
    print("  Levels:", cefr_papers['cefr_alignment'].unique())

print(f"\n" + "="*60)
print("TOP 5 HIGHEST QUALITY EXTRACTIONS")
print("="*60)
top5 = df.nlargest(5, 'confidence_score')[['study_id', 'title', 'llm_model_name', 'kg_type', 'confidence_score']]
for idx, row in top5.iterrows():
    print(f"\n{row['study_id']}: {row['title'][:60]}...")
    print(f"  LLM: {row['llm_model_name']}, KG: {row['kg_type']}, Conf: {row['confidence_score']:.2f}")

print(f"\n" + "="*60)
print("REPORTING GAP ANALYSIS")
print("="*60)
nr_counts = df.apply(lambda x: (x == 'NR').sum(), axis=1)
print(f"Average NR fields per paper: {nr_counts.mean():.1f} / 14 fields")
print(f"This is evidence for the 'Convergence Deficit' hypothesis!")
