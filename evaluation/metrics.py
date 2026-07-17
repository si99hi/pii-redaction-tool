import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import detector

def get_predictions(text: str) -> list:
    """Predict spans."""
    return detector.detect_pii(text)

def main():
    print("Loading models...")
    detector.initialize_detector()
    gt_path = os.path.join(os.path.dirname(__file__), 'ground_truth.json')
    if not os.path.exists(gt_path):
        print(f"Error: Ground truth file not found at {gt_path}")
        return

    with open(gt_path, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)

    total_tp = 0
    total_fp = 0
    total_fn = 0

    cat_stats = {}

    print("Evaluating detector on Prospectus ground truth annotations...\n")

    for idx, item in enumerate(gt_data):
        text = item['text']
        gt_entities = item['entities']
        
        pred_entities = get_predictions(text)
        
        gt_set = {(e['start'], e['end'], e['type']) for e in gt_entities}
        pred_set = {(p['start'], p['end'], p['entity_type']) for p in pred_entities}
        
        tp_set = gt_set.intersection(pred_set)
        fp_set = pred_set.difference(gt_set)
        fn_set = gt_set.difference(pred_set)
        
        total_tp += len(tp_set)
        total_fp += len(fp_set)
        total_fn += len(fn_set)
        
        all_categories = set(list(cat_stats.keys()) + [e['type'] for e in gt_entities] + [p['entity_type'] for p in pred_entities])
        for cat in all_categories:
            cat_stats.setdefault(cat, {'tp': 0, 'fp': 0, 'fn': 0})
            
        for start, end, etype in tp_set:
            cat_stats[etype]['tp'] += 1
        for start, end, etype in fp_set:
            cat_stats[etype]['fp'] += 1
        for start, end, etype in fn_set:
            cat_stats[etype]['fn'] += 1

    print(f"{'Category':<20} | {'TP':<5} | {'FP':<5} | {'FN':<5} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 75)
    for cat, stats in sorted(cat_stats.items()):
        tp = stats['tp']
        fp = stats['fp']
        fn = stats['fn']
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        print(f"{cat:<20} | {tp:<5} | {fp:<5} | {fn:<5} | {precision:<10.2%} | {recall:<10.2%} | {f1:<10.2%}")
    print("-" * 75)

    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0
    
    overall_entity_accuracy = total_tp / (total_tp + total_fp + total_fn) if (total_tp + total_fp + total_fn) > 0 else 0.0

    print("\nOVERALL METRICS:")
    print(f"True Positives (TP): {total_tp}")
    print(f"False Positives (FP): {total_fp}")
    print(f"False Negatives (FN): {total_fn}")
    print(f"Precision:           {overall_precision:.2%}")
    print(f"Recall:              {overall_recall:.2%}")
    print(f"F1-Score:            {overall_f1:.2%}")
    print(f"Entity-level Acc:    {overall_entity_accuracy:.2%} (TP / (TP + FP + FN))")

if __name__ == '__main__':
    main()
