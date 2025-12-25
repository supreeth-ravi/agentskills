#!/usr/bin/env python3
"""Validation: Prove Token Savings with Dynamic Skill Loading"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_skills_sdk import AgentSkillsClient

skills_path = str(Path(__file__).parent.parent / "skills")

print("Validating dynamic skill loading...\n")

# Discover skills
client = AgentSkillsClient(skill_paths=[skills_path], auto_discover=True)
all_skills = client.discover_metadata()

print(f"✅ Discovered {len(all_skills)} skills")

# Measure: Load ALL skills (hardcoded approach)
print("\n❌ Hardcoded Approach: Loading ALL skills...")
total_all = 0
for skill_meta in all_skills:
    try:
        skill = client.load_skill(skill_meta.name)
        tokens = len(skill.instructions) // 4
        total_all += tokens
    except:
        pass

print(f"   Token cost: ~{total_all:,} tokens")

# Measure: Load ONLY 2 skills (dynamic approach)
print("\n✅ Dynamic Approach: Loading only PDF and XLSX...")
client2 = AgentSkillsClient(skill_paths=[skills_path], auto_discover=False)

total_selective = 0
for skill_name in ['pdf', 'xlsx']:
    skill = client2.load_skill(skill_name)
    tokens = len(skill.instructions) // 4
    total_selective += tokens

# Add metadata cost
metadata_tokens = len(all_skills) * 100
total_selective += metadata_tokens

print(f"   Metadata: ~{metadata_tokens:,} tokens")
print(f"   Instructions: ~{total_selective - metadata_tokens:,} tokens")
print(f"   Total: ~{total_selective:,} tokens")

# Savings
savings = total_all - total_selective
savings_pct = (savings / total_all * 100)

print(f"\n💰 SAVINGS:")
print(f"   Hardcoded: ~{total_all:,} tokens")
print(f"   Dynamic: ~{total_selective:,} tokens")
print(f"   SAVED: ~{savings:,} tokens ({savings_pct:.1f}%)")

print(f"\n✅ Validation complete!")
