from argparse import ArgumentParser


def add(a: int, b: int) -> None:
    """Add two numbers."""
    print(f"{a} + {b} = {a + b}")


def main() -> None:
    # define the parser
    parser = ArgumentParser(description="Add two numbers.")

    # add the arguments
    parser.add_argument("a", type=int, help="First number.")
    parser.add_argument("b", type=int, help="Second number.")

    # get the arguments
    args = parser.parse_args()

    # call the function
    add(args.a, args.b)


if __name__ == "__main__":
    main()
