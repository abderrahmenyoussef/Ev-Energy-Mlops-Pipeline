import time
import argparse
import requests

from simulator.scenarios import normal_context, attach_energy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/predict")
    parser.add_argument("--vehicle-id", default="vehicle_001")
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--mode", choices=["normal", "anomaly", "drift"], default="normal")
    parser.add_argument("--rate", type=float, default=1.0, help="requests per second (1.0 = 1 req/sec)")
    args = parser.parse_args()

    interval = 1.0 / args.rate

    print(f"Streaming to: {args.url}")
    print(f"vehicle_id={args.vehicle_id} mode={args.mode} seconds={args.seconds} rate={args.rate}/s")
    print("-" * 80)

    for i in range(args.seconds):
        base = normal_context(args.vehicle_id)
        payload = attach_energy(base, mode=args.mode)

        try:
            r = requests.post(args.url, json=payload, timeout=10)
            r.raise_for_status()
            res = r.json()

            print(
                f"[{i+1:02d}] "
                f"pred={res['predicted_kwh']:.2f} "
                f"act={res['actual_kwh']:.2f} "
                f"res={res['residual_kwh']:.2f} "
                f"err%={res['error_pct']:.1f} "
                f"anom={res['is_anomaly']} alert={res['alert']}"
            )
        except Exception as e:
            print(f"[{i+1:02d}] ERROR: {e}")

        time.sleep(interval)

    print("-" * 80)
    print("Done.")


if __name__ == "__main__":
    main()
