from argus.data.fetch import fetch_all

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    fetch_all("xdviolence", resume=args.resume)
