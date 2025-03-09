import argparse
from api.odoo_client import search_read, create_record, update_record, delete_record

def main():
    parser = argparse.ArgumentParser(description="Consola para interactuar con Odoo")
    parser.add_argument("accion", choices=["search", "create", "update", "delete"], help="Acción a realizar en Odoo")
    parser.add_argument("modelo", help="Modelo de Odoo sobre el cual se ejecutará la acción")
    parser.add_argument("--dominio", type=str, help="Condiciones para búsqueda en formato de lista", default="[]")
    parser.add_argument("--campos", type=str, help="Campos a retornar en una búsqueda", default="[]")
    parser.add_argument("--valores", type=str, help="Valores para creación o actualización en formato JSON", default="{}")
    parser.add_argument("--id", type=int, help="ID del registro a actualizar o eliminar")

    args = parser.parse_args()

    if args.accion == "search":
        resultado = search_read(args.modelo, eval(args.dominio), eval(args.campos))
        print(resultado)

    elif args.accion == "create":
        resultado = create_record(args.modelo, eval(args.valores))
        print(f"Registro creado con ID: {resultado}")

    elif args.accion == "update":
        if not args.id:
            print("Se necesita un ID para actualizar un registro.")
            return
        resultado = update_record(args.modelo, args.id, eval(args.valores))
        print(f"Registro {args.id} actualizado: {resultado}")

    elif args.accion == "delete":
        if not args.id:
            print("Se necesita un ID para eliminar un registro.")
            return
        resultado = delete_record(args.modelo, args.id)
        print(f"Registro {args.id} eliminado: {resultado}")

if __name__ == "__main__":
    main()
