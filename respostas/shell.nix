{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python3
    sqlite
  ];

  shellHook = ''
    echo "🐍 Python $(python3 --version) disponível"
    echo "📦 SQLite $(sqlite3 --version | cut -d' ' -f1) disponível"
    echo ""
    echo "Execute: python3 generate_sql.py"
  '';
}
