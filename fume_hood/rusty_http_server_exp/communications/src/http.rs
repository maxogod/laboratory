use concurrency::thread_pool;
use std::collections::HashMap;
use std::io::{stdin, Read, Write};
use std::net;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;

pub struct Request {
    pub method: String,
    pub path: String,
    // pub headers: HashMap<String, String>,
    pub body: String,
}

pub struct Response {
    pub status_code: u16,
    // pub headers: HashMap<String, String>,
    pub body: String,
}

// Handler is a type alias for a Box that contains a dyn Fn that takes a Request and returns a Response and is thread-safe.
pub type Handler = Box<dyn Fn(Request) -> Response + Send + Sync + 'static>;

pub struct HttpServer {
    address: String,
    routes: Arc<Mutex<HashMap<String, Handler>>>,
    thread_pool: thread_pool::ThreadPool,
}

impl HttpServer {
    pub fn new(address: &str) -> Self {
        return HttpServer {
            address: address.to_string(),
            routes: Arc::new(Mutex::new(HashMap::new())),
            thread_pool: thread_pool::ThreadPool::new(10),
        };
    }

    pub fn add_route(&self, path: &str, handler: Handler) {
        let mut routes = self.routes.lock().unwrap();
        routes.insert(path.to_string(), handler);
    }

    pub fn listen(&self) {
        let listener = net::TcpListener::bind(&self.address).unwrap();

        let stop_signal = Arc::new(AtomicBool::new(false));

        let stop_signal_clone = Arc::clone(&stop_signal);
        let quit_thread = thread::spawn(move || {
            let mut input = String::new();
            stdin().read_line(&mut input).unwrap();
            if input.trim() == "q" {
                stop_signal_clone.store(true, Ordering::SeqCst);
            }
        });

        for stream in listener.incoming() {
            if stop_signal.load(Ordering::SeqCst) {
                break;
            }
            let stream = stream.unwrap();
            let routes = self.routes.clone();
            self.thread_pool.execute(move || {
                Self::handle_connection(stream, routes);
            });
        }

        quit_thread.join().unwrap();
    }

    fn handle_connection(mut stream: net::TcpStream, routes: Arc<Mutex<HashMap<String, Handler>>>) {
        let mut buffer = [0; 1024];
        stream.read(&mut buffer).unwrap();

        let request = String::from_utf8_lossy(&buffer[..]);
        let mut parts = request.split_whitespace();

        let method = parts.next().unwrap();
        let path = parts.next().unwrap();

        if let Some(handler) = routes.lock().unwrap().get(path) {
            let request = Request {
                method: method.to_string(),
                path: path.to_string(),
                body: String::new(),
            };

            let response = handler(request);
            println!("[{}] {} {}", response.status_code, method, path); // log

            let response = format!(
                "HTTP/1.1 {} OK\r\n\r\n{}",
                response.status_code, response.body
            );

            stream.write(response.as_bytes()).unwrap();
            stream.flush().unwrap();
        } else {
            println!("[{}] {} {}", 404, method, path); // log
            let response = "HTTP/1.1 404 NOT FOUND\r\n\r\n";
            stream.write(response.as_bytes()).unwrap();
            stream.flush().unwrap();
        }
    }
}
