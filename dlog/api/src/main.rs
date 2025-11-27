// api/src/main.rs
//
// Minimal Axum HTTP server that exposes:
// - GET /health   : simple health check
// - GET /snapshot : returns a dummy UniverseSnapshot from corelib
//
// Later we will:
// - add auth integration
// - add real endpoints (send, get balance, land, etc.)
// - wire in the ∞ filesystem folding/unfolding.

use std::net::SocketAddr;
use std::sync::{Arc, Mutex};

use axum::{
    extract::State,
    routing::get,
    Json, Router,
};
use corelib::UniverseState;

#[derive(Clone)]
struct AppState {
    universe: Arc<Mutex<UniverseState>>,
}

#[tokio::main]
async fn main() {
    let universe = UniverseState::new();
    let state = AppState {
        universe: Arc::new(Mutex::new(universe)),
    };

    let app = Router::new()
        .route("/health", get(health))
        .route("/snapshot", get(snapshot))
        .with_state(state);

    // Bind to 0.0.0.0 so Docker / other machines can reach this.
    let addr: SocketAddr = "0.0.0.0:8080".parse().unwrap();

    println!("api: listening on http://{addr}");
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .expect("server failed");
}

async fn health() -> &'static str {
    "ok"
}

async fn snapshot(State(state): State<AppState>) -> Json<spec::UniverseSnapshot> {
    let mut guard = state.universe.lock().expect("universe lock poisoned");
    let snapshot = guard.fold_snapshot();
    Json(snapshot)
}
