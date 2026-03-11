import argparse
import sys
# Re-importing from the actual filename I used
from validator_core import EmailValidator

def main():
    parser = argparse.ArgumentParser(description="Verifalia-style Email Validator")
    parser.add_argument("email", nargs="?", help="Single email address to validate")
    parser.add_argument("-f", "--file", help="Path to a file containing email addresses (one per line)")
    parser.add_argument("-o", "--output", help="Path to save results (CSV format)")

    args = parser.parse_args()

    validator = EmailValidator()

    if args.email:
        validate_single(validator, args.email)
    elif args.file:
        validate_batch(validator, args.file, args.output)
    else:
        # Interactive Mode
        print("--- Verifalia-style Email Validator (Interactive Mode) ---")
        print("Type 'exit' or 'quit' to stop.")
        while True:
            try:
                email_input = input("\nEnter email to validate: ").strip()
                if email_input.lower() in ['exit', 'quit']:
                    break
                if not email_input:
                    continue
                validate_single(validator, email_input)
            except KeyboardInterrupt:
                print("\nExiting interactive mode.")
                break
            except EOFError:
                break

def validate_single(validator, email):
    print(f"\nValidating: {email}...")
    result = validator.validate(email)
    
    print("-" * 30)
    print(f"Classification: {result['classification']}")
    print(f"Status Code:    {result['status']}")
    print("-" * 30)
    print(f"Syntax Valid:   {result['is_syntax_valid']}")
    print(f"Disposable:     {result['is_disposable']}")
    print(f"Role Based:     {result['is_role_based']}")
    print(f"MX Records:     {', '.join(result['mx_records']) if result['mx_records'] else 'None'}")
    
    if result["smtp_log"]:
        print("\nLogs:")
        for log in result["smtp_log"]:
            print(f"  - {log}")
    print("-" * 30)

def validate_batch(validator, input_file, output_file):
    try:
        with open(input_file, 'r') as f:
            emails = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print(f"Starting batch validation of {len(emails)} emails...")
    results = []
    
    for i, email in enumerate(emails):
        print(f"[{i+1}/{len(emails)}] {email}...", end="\r")
        results.append(validator.validate(email))
    
    print("\nBatch validation complete.")

    if output_file:
        import csv
        keys = results[0].keys()
        try:
            with open(output_file, 'w', newline='') as f:
                dict_writer = csv.DictWriter(f, keys)
                dict_writer.writeheader()
                dict_writer.writerows(results)
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"Error saving results: {e}")
    else:
        # Summary
        deliverable = sum(1 for r in results if r['classification'] == 'Deliverable')
        undeliverable = sum(1 for r in results if r['classification'] == 'Undeliverable')
        risky = sum(1 for r in results if r['classification'] == 'Risky')
        
        print("\nSummary:")
        print(f"  Deliverable:   {deliverable}")
        print(f"  Undeliverable: {undeliverable}")
        print(f"  Risky:         {risky}")

if __name__ == "__main__":
    main()
