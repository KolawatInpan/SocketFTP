import ftpclient as ftp
client = ftp.Client()

while True:
    try:
        line = input("ftp> ").strip()
        args = line.split()
        if not line:
            continue
        if len(args) == 0:
            continue
        command = args[0]

        if command in ["quit", "bye"]:
            if client.is_connected():
                client.disconnect()
            break

        elif command in ["disconnect", "close"]:
            client.disconnect()

        elif command == "open":
            client.open_ftp(*args[1:])

        elif command == "ascii":
            client.ascii()

        elif command == "binary":
            client.binary()

        elif command == "cd":
            client.cd(args[1] if len(args) > 1 else None)

        elif command == "delete":
            client.delete(args[1] if len(args) > 1 else None)

        elif command == "get":
            client.get(*args[1:]) if len(args) > 1 else client.get()

        elif command == "ls":
            client.ls(*args[1:]) if len(args) > 1 else client.ls()

        elif command == "put":
            client.put(*args[1:]) if len(args) > 1 else client.put()

        elif command == "pwd":
            client.pwd()

        elif command == "mkdir":
            client.mkdir(args[1] if len(args) > 1 else None)

        elif command == "lcd":
            client.lcd(args[1] if len(args) > 1 else None)

        elif command == "rename":
            client.rename(*args[1:]) if len(args) > 1 else client.rename()

        elif command == "user":
            client.authen(
                None, *args[1:]) if len(args) > 1 else client.authen()

        elif command == "connected":
            print(client.is_connected())

        else:
            print("Invalid command.")

    except Exception as e:
        print(e)
        break
