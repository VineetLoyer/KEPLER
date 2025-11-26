#!/usr/bin/env python3
import json
import argparse
from pathlib import Path


def load_config(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def resolve_provider(pricing: dict, key: str):
    # key like "openai.gpt4o_mini"; returns dict with prices
    parts = key.split('.')
    cur = pricing.get('providers', {})
    for p in parts:
        if p not in cur:
            raise KeyError(f"Unknown provider key: {key}")
        cur = cur[p]
    return cur


def estimate_llm_cost(num_claims: float, in_tokens: float, out_tokens: float, pct_images: float,
                      images_per_claim: float, provider_prices: dict) -> dict:
    price_in = provider_prices.get('input_per_1k_tokens_usd', 0.0)
    price_out = provider_prices.get('output_per_1k_tokens_usd', 0.0)
    price_img = provider_prices.get('image_per_image_usd', 0.0)

    llm_in_cost = num_claims * (in_tokens / 1000.0) * price_in
    llm_out_cost = num_claims * (out_tokens / 1000.0) * price_out
    image_calls = num_claims * pct_images * images_per_claim
    image_cost = image_calls * price_img

    return {
        'llm_input_usd': llm_in_cost,
        'llm_output_usd': llm_out_cost,
        'llm_image_usd': image_cost,
        'subtotal_usd': llm_in_cost + llm_out_cost + image_cost
    }


def estimate_ocr_cost(num_claims: float, pct_images: float, images_per_claim: float, per_1k_cost: float,
                      enabled: bool) -> float:
    if not enabled:
        return 0.0
    image_calls = num_claims * pct_images * images_per_claim
    return (image_calls / 1000.0) * per_1k_cost


def estimate_search_cost(num_claims: float, queries_per_claim: float, per_query_cost: float) -> float:
    return num_claims * queries_per_claim * per_query_cost


def main():
    ap = argparse.ArgumentParser(description='Rough LLM API cost estimator for KEPLER Step 1')
    ap.add_argument('--config', type=Path, default=Path('tools/cost_config.json'), help='Path to pricing config JSON')

    # Usage inputs
    ap.add_argument('--num-claims', type=float, required=True, help='Number of claims to process')
    ap.add_argument('--in-toks', type=float, default=300.0, help='Avg input tokens per claim (incl. system+prompt+text)')
    ap.add_argument('--out-toks', type=float, default=120.0, help='Avg output tokens per claim (JSON claims)')
    ap.add_argument('--pct-images', type=float, default=0.2, help='Fraction of claims with an image (0..1)')
    ap.add_argument('--images-per-claim', type=float, default=1.0, help='Avg images per image-bearing claim')

    # Providers and routing
    ap.add_argument('--provider', type=str, default=None, help='Main provider key, e.g., openai.gpt4o_mini')
    ap.add_argument('--premium-provider', type=str, default=None, help='Premium provider key for hard cases, e.g., openai.gpt4o')
    ap.add_argument('--premium-fraction', type=float, default=0.0, help='Fraction of claims routed to premium model (0..1)')

    # OCR/Search
    ap.add_argument('--use-ocr', action='store_true', help='Whether to estimate OCR cost for images')
    ap.add_argument('--ocr-key', type=str, default='vision.azure_vision_read_per_1k', help='Pricing key for OCR per 1k')
    ap.add_argument('--queries-per-claim', type=float, default=2.0, help='Avg search queries per claim')
    ap.add_argument('--search-key', type=str, default='search.google_cse_per_query_usd', help='Pricing key for search per query')

    args = ap.parse_args()

    cfg = load_config(args.config)

    provider_key = args.provider or cfg.get('defaults', {}).get('provider', 'openai.gpt4o_mini')

    def get_nested(d: dict, dotted: str):
        cur = d
        for part in dotted.split('.'):  # we store top-level like providers.search.google_cse_per_query_usd
            if part in cur:
                cur = cur[part]
            else:
                # allow flattened: vision.azure_vision_read_per_1k under providers.vision
                return None
        return cur

    # Resolve providers
    main_prices = resolve_provider(cfg, provider_key)
    premium_prices = resolve_provider(cfg, args.premium_provider) if args.premium_provider else None

    # Resolve OCR/Search unit prices
    vision_prices = cfg['providers'].get('vision', {})
    search_prices = cfg['providers'].get('search', {})
    ocr_per_1k = vision_prices.get(args.ocr_key.split('.')[-1], 0.0) if args.use_ocr else 0.0
    search_per_query = search_prices.get(args.search_key.split('.')[-1], 0.0)

    # Split workload
    num_premium = args.num_claims * max(0.0, min(1.0, args.premium_fraction))
    num_main = args.num_claims - num_premium

    # Main model cost
    main_breakdown = estimate_llm_cost(
        num_main, args.in_toks, args.out_toks, args.pct_images, args.images_per_claim, main_prices
    )

    # Premium model cost (optional)
    premium_breakdown = {'llm_input_usd': 0.0, 'llm_output_usd': 0.0, 'llm_image_usd': 0.0, 'subtotal_usd': 0.0}
    if premium_prices and num_premium > 0:
        premium_breakdown = estimate_llm_cost(
            num_premium, args.in_toks, args.out_toks, args.pct_images, args.images_per_claim, premium_prices
        )

    # Shared costs
    ocr_cost = estimate_ocr_cost(args.num_claims, args.pct_images, args.images_per_claim, ocr_per_1k, args.use_ocr)
    search_cost = estimate_search_cost(args.num_claims, args.queries_per_claim, search_per_query)

    total = main_breakdown['subtotal_usd'] + premium_breakdown['subtotal_usd'] + ocr_cost + search_cost

    def usd(x):
        return f"$ {x:,.2f}"

    print("=== KEPLER Step 1 Cost Estimate ===")
    print(f"Claims: {int(args.num_claims)} | Avg in toks: {args.in_toks} | Avg out toks: {args.out_toks}")
    print(f"Images: {args.pct_images*100:.0f}% of claims | Images/claim: {args.images_per_claim}")
    print(f"Search queries/claim: {args.queries_per_claim}")
    print()
    print(f"Main model ({provider_key}) -> {usd(main_breakdown['subtotal_usd'])} \n  - Input: {usd(main_breakdown['llm_input_usd'])}\n  - Output: {usd(main_breakdown['llm_output_usd'])}\n  - Image: {usd(main_breakdown['llm_image_usd'])}")
    if num_premium > 0:
        print(f"Premium model ({args.premium_provider}) -> {usd(premium_breakdown['subtotal_usd'])} \n  - Input: {usd(premium_breakdown['llm_input_usd'])}\n  - Output: {usd(premium_breakdown['llm_output_usd'])}\n  - Image: {usd(premium_breakdown['llm_image_usd'])}")
    print(f"OCR -> {usd(ocr_cost)}  |  Search -> {usd(search_cost)}")
    print("----------------------------------------")
    print(f"Total -> {usd(total)}")
    print()
    print("Notes:")
    print("- Fill actual unit prices in tools/cost_config.json from your provider dashboards.")
    print("- Token counts are model-dependent and prompt-dependent; measure with provider tokenizers.")
    print("- Premium fraction routes hard cases to a more accurate but costlier model.")


if __name__ == '__main__':
    main()
