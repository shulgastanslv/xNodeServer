from __future__ import annotations

import asyncio
import http
import logging
import typing

import routes
import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoutedPath(str):
    """Represents a path matched to a route with parameters and context."""
    route: typing.Any
    params: typing.Mapping[str, str]
    context: typing.MutableMapping[typing.Any, typing.Any]

    @classmethod
    def create(cls, raw_path: str, route: typing.Any, params: typing.Mapping[str, str]) -> RoutedPath:
        """Factory method to create a RoutedPath instance."""
        path = cls(raw_path)
        path.route = route
        path.params = params
        path.context = {}
        logger.debug(f"Created RoutedPath: path={path}, route={route}, params={params}")
        return path


class Protocol(websockets.WebSocketServerProtocol):
    """Server protocol with routing support."""
    
    def __init__(self, router: Router, *args, **kwargs):
        if not isinstance(router, Router):
            raise TypeError("router must be an instance of the Router class")
        
        self._router = router
        super().__init__(*args, **kwargs)
        logger.info(f"Protocol initialized with router: {router}")


    async def read_http_request(self) -> typing.Tuple[RoutedPath, websockets.http.Headers]:
        """Read and match the HTTP request path using the router."""
        raw_path, headers = await super().read_http_request()
        if isinstance(self._router, Router):
            return self._router.match(raw_path), headers
        raise TypeError("Expected self._router to be an instance of Router")

    async def process_request(self, path: RoutedPath, headers: websockets.http.Headers) -> typing.Optional[typing.Tuple[http.HTTPStatus, list, bytes]]:
        """Process the request if the route defines a process_request method."""
        if path.params is None:
            logger.warning(f"Request path not found: {path}")
            return http.HTTPStatus.NOT_FOUND, [], b"not found\n"
        
        process_request = getattr(path.route, "process_request", None)
        if process_request is None:
            logger.info(f"No process_request method found for route: {path.route}")
            return None
        logger.info(f"Processing request for path: {path}")
        response = await process_request(path, headers)
        if response and not isinstance(response[0], http.HTTPStatus):
            response = (http.HTTPStatus(response[0]), *response[1:])
        logger.debug(f"Processed response: {response}")
        return response


class Router:
    """Router class to manage route matching and handling."""

    def __init__(self):
        self._mapper = routes.Mapper()

    async def __call__(self, ws: websockets.WebSocketCommonProtocol, path: RoutedPath):
        """Handle incoming WebSocket requests."""
        if not isinstance(path, RoutedPath):
            path = self.match(path)

        if path.params is None:
            logger.warning(f"Closing WebSocket for unmatched path: {path}")
            await ws.close(1000)
            return

        handle = getattr(path.route, "handle", None)
        if handle is None:
            logger.info(f"No handle method found for route: {path.route}")
            return
        logger.info(f"Handling WebSocket request for path: {path}")
        await handle(ws, path)

    def route(self, path: str, *, name: typing.Optional[str] = None):
        """Decorator for routing paths to endpoints."""
        def decorator(endpoint: typing.Callable[[], typing.Any]):
            if not asyncio.iscoroutinefunction(endpoint):
                route_cls = endpoint
            else:
                route_cls = type(endpoint.__name__, (), {"handle": staticmethod(endpoint)})
            
            self._mapper.connect(name, path, __route_cls=route_cls)
            return endpoint
        return decorator
    
    def _match_route_cls(self, params: typing.Optional[typing.Mapping[str, typing.Any]]) -> typing.Optional[typing.Any]:
        if params is None:
            return None
        return params.pop("__route_cls", None)()

    def match(self, path: str) -> RoutedPath:
        """Match a path to a route and return a RoutedPath object."""
        params = self._mapper.match(path)
        route = self._match_route_cls(params)
        return RoutedPath.create(path, route, params)

    async def serve(self, host: str, port: int, *args, **kwargs) -> websockets.server.Serve:
        logger.info(f"Starting WebSocket server on {host}:{port}")
        return await websockets.serve(
            ws_handler=self,
            host=host,
            port=port,
            create_protocol=lambda *a, **kw: Protocol(self, *a, **kw),
            *args,
            **kwargs,
        )
