"""Metin raporları için basit SWOT analizörü.

Bu betik, metni cümlelere bölerek, anahtar kelimelerle eşleştirerek,
her SWOT kategorisine puan verip cümleleri sınıflandıran ve sayısal
metrikleri (sıcaklıklar, akımlar, gerilimler) çıkaran hafif, kural
tabanlı bir analiz yapar.

Kullanım:
    python -m sim.swot_analyzer --input-file sim/sample_report.txt --output-json sim/swot_output_example.json

Bu uygulama dışa bağımlılık gerektirmez ve çevrimdışı çalışır.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple


SENT_SPLIT_RE = re.compile(r"(?<=[.!?\n])\s+")


@dataclass
class SWOTResult:
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    metrics: Dict[str, List[str]]


class SWOTAnalyzer:
    def __init__(self) -> None:
        # anahtar kelime sözlükleri (küçük harfli eşleşme için)
        self.keywords = {
            "strengths": [
                "kimlik doğrulama",
                "nominal",
                "akım azalt",
                "güvenlik",
                "politika",
                "standart",
                "kalibrasyon",
                "izleme",
            ],
            "weaknesses": [
                "demir",
                "uygunsuz",
                "yüksek temas direnci",
                "aşırı ısınma",
                "sıcaklık",
                "kayıp",
                "verim",
                "sarkma",
                "korozyon",
                "şüphe",
            ],
            "opportunities": [
                "sensör",
                "bakım",
                "kalibrasyon",
                "güncelleme",
                "doğrula",
                "doğrulama",
                "beyaz liste",
                "kara liste",
                "test",
                "eğitim",
            ],
            "threats": [
                "kritik",
                "yangın",
                "zarar",
                "kapanma",
                "tehlike",
                "kullanılamaz",
                "kilitlenme",
                "stoptransaction",
                "yüksek sıcaklık",
            ],
        }

    def split_sentences(self, text: str) -> List[str]:
        # basit cümle ayırıcı (kırılma karakterlerine göre)
        parts = [s.strip() for s in SENT_SPLIT_RE.split(text) if s.strip()]
        # further split very long lines by periods if needed
        sentences: List[str] = []
        for p in parts:
            if len(p) > 400:
                sentences.extend([s.strip() for s in p.split('.') if s.strip()])
            else:
                sentences.append(p)
        return sentences

    def score_sentence(self, sentence: str) -> Dict[str, int]:
        s = sentence.lower()
        scores = {k: 0 for k in self.keywords}
        for cat, kws in self.keywords.items():
            for kw in kws:
                if kw in s:
                    scores[cat] += 1
        return scores

    def extract_metrics(self, text: str) -> Dict[str, List[str]]:
        metrics: Dict[str, List[str]] = defaultdict(list)
        # sıcaklık örnekleri: 86.3C veya 86.3 C veya 86C
        for m in re.findall(r"(\d{1,3}(?:\.\d+)?)[ ]?°?C\b", text, flags=re.IGNORECASE):
            metrics["temperatures"].append(f"{m}C")
        # currents like 28.5A or 32 A
        for m in re.findall(r"(\d{1,3}(?:\.\d+)?)[ ]?A\b", text, flags=re.IGNORECASE):
            metrics["currents"].append(f"{m}A")
        # gerilim örnekleri: 230V
        for m in re.findall(r"(\d{1,4}(?:\.\d+)?)[ ]?V\b", text, flags=re.IGNORECASE):
            metrics["voltages"].append(f"{m}V")
        return metrics

    def analyze(self, text: str) -> SWOTResult:
        sentences = self.split_sentences(text)
        buckets = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
        for sent in sentences:
            scores = self.score_sentence(sent)
            # choose category with highest score > 0
            best_cat, best_score = max(scores.items(), key=lambda kv: kv[1])
            if best_score > 0:
                buckets[best_cat].append(sent)
        metrics = dict(self.extract_metrics(text))

        # deduplicate while preserving order
        def uniq(seq: List[str]) -> List[str]:
            seen = set()
            out: List[str] = []
            for s in seq:
                if s not in seen:
                    seen.add(s)
                    out.append(s)
            return out

        return SWOTResult(
            strengths=uniq(buckets["strengths"]),
            weaknesses=uniq(buckets["weaknesses"]),
            opportunities=uniq(buckets["opportunities"]),
            threats=uniq(buckets["threats"]),
            metrics=metrics,
        )


def pretty_print(result: SWOTResult) -> None:
    def print_block(title: str, items: List[str]) -> None:
        print(f"\n{title}:\n")
        if not items:
            print("  - (yok)")
        for s in items:
            print(f"  - {s}")

    print_block("Güçlü Yönler", result.strengths)
    print_block("Zayıf Yönler", result.weaknesses)
    print_block("Fırsatlar", result.opportunities)
    print_block("Tehditler", result.threats)
    print("\nÇıkarılan metrikler:")
    if not result.metrics:
        print("  - (yok)")
    for k, vals in result.metrics.items():
        print(f"  {k}: {', '.join(vals)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Basit SWOT analizörü (raporlara yönelik)")
    parser.add_argument("--input-file", type=str, required=True)
    parser.add_argument("--output-json", type=str, default=None)
    args = parser.parse_args()

    p = Path(args.input_file)
    if not p.exists():
        raise SystemExit(f"Input file not found: {p}")
    text = p.read_text(encoding="utf-8")
    analyzer = SWOTAnalyzer()
    result = analyzer.analyze(text)
    pretty_print(result)

    if args.output_json:
        out = Path(args.output_json)
        out.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON çıktısı yazıldı: {out}")


if __name__ == "__main__":
    main()
