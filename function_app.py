import azure.functions as func
from linkedIn import master

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="scrape", methods=["Post"], auth_level=func.AuthLevel.ANONYMOUS
)
def api_scrape(req: func.HttpRequest) -> func.HttpResponse:
    content = req.params
    # Expecting "profile_urls" to be a list of URLs.
    profile_urls = content.get("profile_urls")

    if not profile_urls:

         return func.HttpResponse(
            "Profile URL list is required",
            status_code=400,
        )
    try:
        # Now passing a dictionary with "profile_urls" as expected by the master function.
        data = master({"profile_urls": profile_urls})
        return func.HttpResponse(
            data,
            headers={"Content-Type": "application/json"},
        )
    except Exception as e:
        return func.HttpResponse(str(e), status_code=500)
