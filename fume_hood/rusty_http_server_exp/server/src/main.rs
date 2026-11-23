use communications::http;

fn main() {
    println!("Server started.");
    let http = http::HttpServer::new("127.0.0.1:8080");

    // routes
    http.add_route("/", Box::new(get_home));
    http.add_route("/hello", Box::new(get_hello));

    http.listen();
}

// My routes

fn get_home(_request: http::Request) -> http::Response {
    return http::Response {
        status_code: 200,
        body: "Hello, world!".to_string(),
    };
}

fn get_hello(_request: http::Request) -> http::Response {
    return http::Response {
        status_code: 200,
        body: "Hello!".to_string(),
    };
}
