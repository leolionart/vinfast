import urllib.request
import urllib.error
import ssl

REGIONS = {
    "VN": {
        "auth0": "https://vin3s.au.auth0.com/.well-known/openid-configuration",
        "api": "https://mobile.connected-car.vinfast.vn/ccarusermgnt/api/v1/user-vehicle"
    },
    "US": {
        "auth0": "https://vinfast-us-prod.us.auth0.com/.well-known/openid-configuration",
        "api": "https://mobile.connected-car.vinfastauto.us/ccarusermgnt/api/v1/user-vehicle"
    },
    "EU": {
        "auth0": "https://vinfast-eu-prod.eu.auth0.com/.well-known/openid-configuration",
        "api": "https://mobile.connected-car.vinfastauto.eu/ccarusermgnt/api/v1/user-vehicle"
    }
}

def check_url(name, url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        # Create unverified context to avoid SSL cert issues in some environments
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context, timeout=10) as response:
            status = response.getcode()
            print(f"[{status}] {name}: {url}")
            return status
    except urllib.error.HTTPError as e:
        status = e.code
        # 401/403 is EXPECTED for API calls without token -> Server is UP
        print(f"[{status}] {name}: {url}")
        return status
    except Exception as e:
        print(f"[ERR] {name}: {e}")
        return None

def main():
    print("Checking VinFast API Endpoints...")
    print("-" * 50)
    
    for region, urls in REGIONS.items():
        print(f"\n--- Region: {region} ---")
        # Check Auth0
        check_url(f"Auth0 ({region})", urls["auth0"])
        
        # Check User Vehicle API
        check_url(f"API Core ({region})", urls["api"])

if __name__ == "__main__":
    main()
