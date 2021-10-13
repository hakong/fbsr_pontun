export function sort(a, b) {
	if (a === null)
		return -1;
	else if (b === null)
		return 1;
	else if (typeof a === "string")
		return a.toLowerCase().localeCompare(b.toLowerCase());
	else if (a === b)
		return 0;
	else
		return a > b ? 1 : -1;
}

export function CaretDown(props) {
	return (
		<svg width="1em" height="1em" viewBox="0 0 16 16" className="bi bi-caret-down-fill" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
			<path d="M7.247 11.14L2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"/>
		</svg>
	);
}

export function CaretUp(props) {
	return (
		<svg width="1em" height="1em" viewBox="0 0 16 16" className="bi bi-caret-up-fill" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
			<path d="M7.247 4.86l-4.796 5.481c-.566.647-.106 1.659.753 1.659h9.592a1 1 0 0 0 .753-1.659l-4.796-5.48a1 1 0 0 0-1.506 0z"/>
		</svg>
	);
}
