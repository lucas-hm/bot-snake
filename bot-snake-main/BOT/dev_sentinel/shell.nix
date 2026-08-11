{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  # 1. Paquetes que querés dentro del entorno
  buildInputs = with pkgs; [
    python3
    python312Packages.pip
    python312Packages.virtualenv # Opcional, pero útil para aislar más
    mariadb
    sqlite
    # Librerías de sistema que Python suele necesitar (ej: para pandas o opencv)
    stdenv.cc.cc.lib
    libz
    (python3.withPackages (ps: with ps; [
      pymongo        # Driver oficial para MongoDB
      mysqlclient    # Driver eficiente para MariaDB/MySQL
      # (SQLite ya viene incorporado dentro del propio Python)
    ]))

    nodejs
    pkg-config
    openssl
  ];

  # 2. Comandos que se ejecutan automáticamente al entrar al shell
  shellHook = ''
    echo "⚽ Entrando al entorno de desarrollo de Morandona..."

    # Crear un entorno virtual de Python si no existe
    if [ ! -d ".venv" ]; then
      python -m venv .venv
      echo "🐍 Entorno virtual creado."
    fi

    # Activarlo automáticamente
    source .venv/bin/activate

    # Exportar variables para que las librerías de C funcionen bien en Nix
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"

    echo "🔥 Estás listo. Usá 'pip install' tranquilo dentro de este shell."
  '';
}
