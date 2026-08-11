{ pkgs ? import <nixpkgs> {} }:

let
  pythonPackages = pkgs.python312Packages;
in
pkgs.mkShell rec {
  name = "morandonaEnv";
  venvDir = "./.venv";

  buildInputs = with pkgs; [
    # Intérprete de Python y Hooks para Venv automático de Nix
    pythonPackages.python
    pythonPackages.venvShellHook

    # Paquetes de Python administrados por Nixpkgs (cargan directo al PYTHONPATH)
    pythonPackages.pip
    pythonPackages.numpy
    pythonPackages.requests
    pythonPackages.pymongo
    pythonPackages.mysqlclient

    # Herramientas de desarrollo y Bases de Datos
    mariadb
    sqlite
    nodejs
    pkg-config
    git

    # Librerías C y del sistema requeridas para compilar/ejecutar wheels con pip
    stdenv.cc.cc.lib
    openssl
    taglib
    libxml2
    libxslt
    libzip
    zlib
  ];

  # Se ejecuta la primera vez que Nix crea el entorno virtual (.venv)
  postVenvCreation = ''
    unset SOURCE_DATE_EPOCH
    if [ -f requirements.txt ]; then
      echo "📦 Instalando dependencias desde requirements.txt..."
      pip install -r requirements.txt
    fi
  '';

  # Se ejecuta CADA VEZ que entrás al nix-shell
  postShellHook = ''
    unset SOURCE_DATE_EPOCH
    
    # Corrige problemas de librerías dinámicas de C para paquetes como OpenCV, Pandas, etc.
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH"

    echo "⚽ Entrando al entorno de desarrollo..."
    echo "🔥 Entorno virtual activado. Podés usar 'pip install' tranquilamente."
  '';
}