import 'bootstrap/dist/css/bootstrap.min.css';

import React from 'react';
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link,
	NavLink,
	Redirect
} from "react-router-dom";
import ReactDOM from 'react-dom';
import {sort, CaretUp, CaretDown} from './misc.js';
import {PaymentsPage} from './payments.js';
import {ShipmentPage} from './shipments.js';
import './index.css';


class NotFound extends React.Component {
	render() {
		return (
			<h2>Not found</h2>
		);
	}
}


class Wrapper extends React.Component {
	render() {
		return (
			<Router>
				<Switch>
					<Route path="/a" component={App} />
					<Route component={NotFound} />
				</Switch>
			</Router>
		);
	}
}


class App extends React.Component {
	render() {
		const { match } = this.props;

		return (
			<div>
				<header>	
					<nav className="navbar navbar-expand-md navbar-dark fixed-top bg-dark">
						<Link className="navbar-brand" to={{pathname: match.url, search: window.location.search}}>Pantanir</Link>
					</nav>
				</header>
				<main className="container-fluid">
					<Switch>
						<Route path={`${match.url}/listing/:listingId`} component={Listing} />
						<Route path={match.url} component={Listings} />
					</Switch>
				</main>
			</div>
		);
	}
}

class MemberEntry extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			details_visible: false,
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token")
		}
		this.handleClick     = this.handleClick.bind(this);
		this.handleConfirm   = this.handleConfirm.bind(this);
		this.handleUnconfirm = this.handleUnconfirm.bind(this);
		this.handleClear     = this.handleClear.bind(this);
	}

	handleClick(event) { this.setState({details_visible: ~this.state.details_visible}); }
	handleConfirm(event) { 
		let self = this;
		if (window.confirm("Viltu staðfesta pöntun viðkomandi?")) {
			fetch("/api/confirm", {method: "PUT", headers: {'Authorization': this.state.auth_token, 'Content-Type': 'application/json'}, body: JSON.stringify({member_id: this.props.member.id})})
				.then(res => res.json())
				.then(
					(results) => self.props.reload()
				);
		}
		event.stopPropagation();
		event.preventDefault();
	}
	handleUnconfirm(event) { 
		let self = this;
		if (window.confirm("Viltu opna (gera óstaðfesta) pöntun?")) {
			fetch("/api/unconfirm", {method: "PUT", headers: {'Authorization': this.state.auth_token, 'Content-Type': 'application/json'}, body: JSON.stringify({member_id: this.props.member.id})})
				.then(res => res.json())
				.then(
					(results) => self.props.reload()
				);
		}
		event.stopPropagation();
		event.preventDefault();
	}
	handleClear(event) {
		let self = this;
		if (window.confirm("Viltu hreinsa körfu viðkomandi? Þetta er ekki afturkræft!")) {
			fetch("/api/clear", {method: "PUT", headers: {'Authorization': this.state.auth_token, 'Content-Type': 'application/json'}, body: JSON.stringify({member_id: this.props.member.id})})
				.then(res => res.json())
				.then(
					(results) => self.props.reload()
				);
		}
		event.stopPropagation();
		event.preventDefault();
	}

	render() {
		const clr = this.props.member.qty > 0 ? (this.props.member.confirmed !== null ? 'table-success' : 'table-warning') : '';
		let frmt = new Intl.DateTimeFormat("is-IS", { year: "numeric", month: "short", day: "numeric", hour: 'numeric', minute: 'numeric'});

		let details = null;
		if (this.state.details_visible && this.props.member.hasOwnProperty("entries")) {
		let entries = this.props.member.entries.map((val, idx) => <OrderEntry marker={false} entry={val} />);
		details = <tr><td colSpan="9"><table className="mx-auto my-2 table table-striped table-hover table-sm">
			<thead>
				<tr>
					<th  key="vendor_id">#</th>
					<th  key="item_name">Hlutur</th>
					<th  key="price"    >Verð {this.props.currency} / ISK</th>
					<th  key="qty"      >Magn</th>
					<th  key="total"    >Samtals {this.props.currency} / ISK</th>
				</tr>
			</thead>
			{entries}
		</table></td></tr>
	}
	let actions = <td key="actions"></td>;
	if (this.props.member.hasOwnProperty("entries")) {
		actions = <td key="actions">
				<button className="btn mx-1 btn-sm btn-warning" onClick={this.handleUnconfirm} disabled={this.props.member.confirmed === null}>Opna</button>
				<button className="btn mx-1 btn-sm btn-warning" onClick={this.handleConfirm} disabled={this.props.member.confirmed !== null}>Staðfesta</button>
				<button className="btn mx-1 btn-sm btn-danger" onClick={this.handleClear} disabled={this.props.member.confirmed !== null}>Núlla</button>
			</td>
	}

	return <tbody><tr className={clr} onClick={this.handleClick}>
			<td key="name">{this.props.member.name}</td>
			<td key="email">{this.props.member.email}</td>
			<td key="locked">{this.props.member.locked === null? 'Nei' : frmt.format(Date.parse(this.props.member.locked))}</td>
			<td key="confirmed">{this.props.member.confirmed === null? 'Nei' : frmt.format(Date.parse(this.props.member.confirmed))}</td>
			<td key="last_movement">{this.props.member.last_movement === null? 'Aldrei opnað' : frmt.format(Date.parse(this.props.member.last_movement))}</td>
			<td key="signup">{frmt.format(Date.parse(this.props.member.signup))}</td>
			<td key="qty">{this.props.member.qty}</td>
			<td key="total">{this.props.member.fk_total.toLocaleString()} / {this.props.member.isk_total.toLocaleString()}</td>
			{actions}
		</tr>{details}</tbody>;
}
}


class OrderEntry extends React.Component {
	constructor(props) {
		super(props);
		this.state = {details_visible: false};
		this.handleClick = this.handleClick.bind(this);
		this.handleMark  = this.handleMark.bind(this);
	}

	handleClick(event) {
		this.setState({details_visible: ~this.state.details_visible});
	}

	handleMark(event) {
		console.log("handleMark(", event, ") for id ", this.props.entry.id);
		this.props.toggleMark(this.props.entry.id);
		event.stopPropagation();
	}

	render() {
		console.log("rendering order list");
		let details = null;
		if (this.state.details_visible && this.props.entry.hasOwnProperty("members")) {
			let entries = this.props.entry.members.map((val, idx) => <MemberEntry key={idx} member={val} />);
			details = <tr><td colSpan="9"><table className="mx-auto my-2 table table-striped table-hover table-sm">
				<thead>
					<tr>
						<th key="name"         >Nafn             </th>
						<th key="email"        >Netfang          </th>
						<th key="locked"       >Karfa læst       </th>
						<th key="confirmed"    >Karfa staðfest   </th>
						<th key="last_movement">Síðasta hreyfing </th>
						<th key="signup"       >Skráning         </th>
						<th key="qty"          >Fjöldi hluta     </th>
						<th key="total"        >Samtals {this.props.currency} / ISK</th>
					</tr>
				</thead>
				{entries}
			</table></td></tr>
		}

		let member_button = null;
		if (this.props.entry.hasOwnProperty("members")) {
			let more_text = this.state.details_visible ? "Fela kaupendur" : "Sjá kaupendur";
			member_button = <button type="button" onClick={this.handleClick} className="btn btn-sm btn-info mx-2">{more_text}</button>;
		}

		let properties = null;
		let br = null;
		if (this.props.entry.properties.length > 0) {
			const _props = this.props.entry.properties.map((value, key) => <li className="list-inline-item small" key={value.adjusted}><span>{value.adjusted}: </span><span className="font-weight-bold">{value.value}</span></li>).reduce((acc, x) => acc === null ? [x] : [acc, '| ', x], null);
			properties = <ul className="list-inline">{_props}</ul>;
			br = <br />;
		}
		let marker = null;
		if (this.props.entry.hasOwnProperty("marked")) {
			marker = <td key="marker"><input name={this.props.entry.id} type="checkbox" defaultValue={false} onChange={this.handleMark} checked={this.props.entry.marked}></input></td>;
		}
		return <tbody><tr>
				{marker}
				<td key="vendor_id">{this.props.entry.vendor_id}</td>
				<td key="name"><a href={this.props.entry.url}>{this.props.entry.item_name}</a> {member_button} {br} {properties} </td>
				<td key="price">{this.props.entry.price.toLocaleString()} / {this.props.entry.price_isk.toLocaleString()}</td>
				<td key="qty">{this.props.entry.qty}</td>
				<td key="total">{this.props.entry.fk_total.toLocaleString()} / {this.props.entry.isk_total.toLocaleString()}</td>
			</tr>{details}</tbody>
	}
}

class MemberList extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token"),
			memberSortColumn: "name",
			memberSortColumnDirection: "asc",
			members: null,
		}
		this.handleMemberSort = this.handleMemberSort.bind(this);
		this.reload  = this.reload.bind(this);
	}

	reload() {
		fetch("/api/listing/" + this.props.listing.id + "/members", {headers: {'Authorization': this.state.auth_token}})
			.then(res => res.json())
			.then(
				(results) => this.setState(results)
			);
	}

	componentDidMount() { this.reload(); }

	handleMemberSort(key) {
		if (key === this.state.memberSortColumn) {
			this.setState({"memberSortColumnDirection": this.state.memberSortColumnDirection === "asc" ? "desc" : "asc"});
		} else {
			this.setState({"memberSortColumn": key, "memberSortColumnDirection": "asc"});
		}
	}

	render() {
		if (this.state.members === null)
			return "";

		const { match } = this.props;

		console.log(this.state.members, this.state.members.sort);
		const member_rows   = this.state.members
			.sort((a, b) => (this.state.memberSortColumnDirection === "asc" ? 1 : -1)*sort(a[this.state.memberSortColumn], b[this.state.memberSortColumn]))
			.map((value, key) => <MemberEntry reload={this.reload} currency={this.props.listing.currency} match={match} key={value.id} member={value} />);

		const confirmed_qty = this.state.members.map((value) => value.confirmed === null ? 0 : value.qty      ).reduce((a,b) => a+b, 0);
		const total_qty     = this.state.members.map((value) => value.qty                                     ).reduce((a,b) => a+b, 0);
		const confirmed_fk  = this.state.members.map((value) => value.confirmed === null ? 0 : value.fk_total ).reduce((a,b) => a+b, 0);
		const total_fk      = this.state.members.map((value) => value.fk_total                                ).reduce((a,b) => a+b, 0);
		const confirmed_isk = this.state.members.map((value) => value.confirmed === null ? 0 : value.isk_total).reduce((a,b) => a+b, 0);
		const total_isk     = this.state.members.map((value) => value.isk_total                               ).reduce((a,b) => a+b, 0);

		return (
			<div>
				<h3>Nafnalisti</h3>
				<table className="table table-striped table-hover table-sm">
					<thead>
						<tr>
							<th onClick={() => this.handleMemberSort('name')}          key="name"         >Nafn             {this.state.memberSortColumn === "name"          ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleMemberSort('email')}         key="email"        >Netfang          {this.state.memberSortColumn === "email"         ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleMemberSort('locked')}        key="locked"       >Karfa læst       {this.state.memberSortColumn === "locked"        ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleMemberSort('confirmed')}     key="confirmed"    >Karfa staðfest   {this.state.memberSortColumn === "confirmed"     ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleMemberSort('last_movement')} key="last_movement">Síðasta hreyfing {this.state.memberSortColumn === "last_movement" ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleMemberSort('signup')}        key="signup"       >Skráning         {this.state.memberSortColumn === "signup"        ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleMemberSort('qty')}           key="qty"          >Fjöldi hluta     {this.state.memberSortColumn === "qty"           ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleMemberSort('isk_total')}     key="total"        >Samtals {this.props.listing.currency} / ISK {this.state.memberSortColumn === "isk_total" ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
								<th></th>
							</tr>
						</thead>
						{member_rows}
						<tfoot>
							<tr key="total">
								<th key="txt" colSpan="6">Samtals í körfum (staðfest og óstaðfest)</th>
								<th key="qty">{total_qty.toLocaleString()}</th>
								<th key="total">{total_fk.toLocaleString()} / {total_isk.toLocaleString()}</th>
								<th></th>
							</tr>
							<tr key="confirmed">
								<th key="txt" colSpan="6">Samtals staðfest</th>
								<th key="qty">{confirmed_qty.toLocaleString()}</th>
								<th key="total">{confirmed_fk.toLocaleString()} / {confirmed_isk.toLocaleString()}</th>
								<th></th>
							</tr>
						</tfoot>
					</table>
			</div>
		);
	}
}

class OrderList extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token"),
			order: null, 
			orderSortColumn: "name",
			orderSortColumnDirection: "asc",
		};
		this.handleOrderSort  = this.handleOrderSort.bind(this);
		this.toggleMark  = this.toggleMark.bind(this);
		this.reload  = this.reload.bind(this);
	}

	reload() {
		fetch("/api/listing/" + this.props.listing.id + "/order", {headers: {'Authorization': this.state.auth_token}})
			.then(res => res.json())
			.then(
				(results) => this.parseState(results) //this.setState(results)
			);
	}

	parseState(results) {
		console.log("reloading");
		results.order = results.order.map((value) => Object.assign({}, JSON.parse(JSON.stringify(value)), {marked: false}));
		this.setState(results);
	}

	componentDidMount() {
		this.reload();
	}

	handleOrderSort(key) {
		if (key === this.state.orderSortColumn) {
			this.setState({"orderSortColumnDirection": this.state.orderSortColumnDirection === "asc" ? "desc" : "asc"});
		} else {
			this.setState({"orderSortColumn": key, "orderSortColumnDirection": "asc"});
		}
	}

	toggleMark(entry_id) {
		let order = JSON.parse(JSON.stringify(this.state.order));
		order.forEach((value, idx) => {
			if (value.id === entry_id) {
				console.log("order[", idx, "] went from ", value.marked, " to ", !value.marked);
				order[idx].marked = !value.marked;
			}
		});
		this.setState({order: order});
		console.log("uppfaeri state");
	}

	render() {
		if (this.state.order === null)
			return "Missing state entry: order";

		const { match } = this.props;

		const order_rows    = this.state.order.sort((a, b) =>   (this.state.orderSortColumnDirection  === "asc" ? 1 : -1)*sort(a[this.state.orderSortColumn ], b[this.state.orderSortColumn ])).map((value, key) => <OrderEntry toggleMark={this.toggleMark} marker={false} reload={this.reload} currency={this.props.listing.currency} match={match} key={value.id} entry={value} />);

		const confirmed_qty = this.state.order.map((value) => value.confirmed === null ? 0 : value.qty      ).reduce((a,b) => a+b, 0);
		const confirmed_fk  = this.state.order.map((value) => value.confirmed === null ? 0 : value.fk_total ).reduce((a,b) => a+b, 0);
		const confirmed_isk = this.state.order.map((value) => value.confirmed === null ? 0 : value.isk_total).reduce((a,b) => a+b, 0);
		const marked_qty    = this.state.order.filter((value) => value.marked).map((value) => value.confirmed === null ? 0 : value.qty      ).reduce((a,b) => a+b, 0);
		const marked_fk     = this.state.order.filter((value) => value.marked).map((value) => value.confirmed === null ? 0 : value.fk_total ).reduce((a,b) => a+b, 0);
		const marked_isk    = this.state.order.filter((value) => value.marked).map((value) => value.confirmed === null ? 0 : value.isk_total).reduce((a,b) => a+b, 0);

		return (
			<div>
				<h3>Pöntunarlisti</h3>
				<table className="table table-striped table-hover table-sm">
					<thead>
						<tr> 
							<th key="marker"></th>
							<th onClick={() => this.handleOrderSort('vendor_id')} key="vendor_id"># {this.state.orderSortColumn === "vendor_id" ? (this.state.orderSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleOrderSort('item_name')} key="item_name">Hlutur {this.state.orderSortColumn === "item_name" ? (this.state.orderSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleOrderSort('price')}     key="price"    >Verð {this.props.listing.currency} / ISK {this.state.orderSortColumn === "price" ? (this.state.orderSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleOrderSort('qty')}       key="qty"      >Magn {this.state.orderSortColumn === "qty" ? (this.state.orderSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
							<th onClick={() => this.handleOrderSort('isk_total')} key="total"    >Samtals {this.props.listing.currency} / ISK {this.state.orderSortColumn === "isk_total" ? (this.state.orderSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
						</tr>
					</thead>
					{order_rows}
					<tfoot>
						<tr key="order-totals">
							<th key="marker"></th>
							<th key="txt" colSpan="3">Samtals staðfest</th>
							<th key="qty">{confirmed_qty.toLocaleString()}</th>
							<th key="total">{confirmed_fk.toLocaleString()} / {confirmed_isk.toLocaleString()}</th>
						</tr>
						<tr key="marked-totals">
							<th key="marker"></th>
							<th key="txt" colSpan="3">Merkt samtala</th>
							<th key="qty">{marked_qty.toLocaleString()}</th>
							<th key="total">{marked_fk.toLocaleString()} / {marked_isk.toLocaleString()}</th>
						</tr>
					</tfoot>
				</table>
			</div>
		);
	}
}

class Listing extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token"),
			listing: null,
		};
		this.reload  = this.reload.bind(this);
	}

	reload() {
		fetch("/api/listing/" + this.props.match.params.listingId, {headers: {'Authorization': this.state.auth_token}})
			.then(res => res.json())
			.then(
				(results) => this.setState(results)
			);
	}

	componentDidMount() {
		this.reload();
	}



	render() {
		if (this.state.listing === null)
			return "";

		const { match } = this.props;

		return (
			<div className="pt-5 mt-2">
				<h2>Pöntun: {this.state.listing.title}</h2>
				<ul className="nav nav-tabs">
					<li className="nav-item"><NavLink activeClassName="active" className="nav-link" to={{pathname: `${match.url}/info`, search: this.props.location.search}}>Pöntun</NavLink></li>
					<li className="nav-item"><NavLink activeClassName="active" className="nav-link" to={{pathname: `${match.url}/members`, search: this.props.location.search}}>Meðlimir</NavLink></li>
					<li className="nav-item"><NavLink activeClassName="active" className="nav-link" to={{pathname: `${match.url}/order`, search: this.props.location.search}}>Pöntunarlisti</NavLink></li>
					<li className="nav-item"><NavLink activeClassName="active" className="nav-link" to={{pathname: `${match.url}/shipments`, search: this.props.location.search}}>Sendingar</NavLink></li>
					<li className="nav-item"><NavLink activeClassName="active" className="nav-link" to={{pathname: `${match.url}/payments`, search: this.props.location.search}}>Uppgjör</NavLink></li>
				</ul>
				<Switch>
					<Route path={`${match.url}/members`}>
						<MemberList listing={this.state.listing} />
					</Route>
					<Route path={`${match.url}/order`}>
						<OrderList  listing={this.state.listing} />
					</Route>
					<Route path={`${match.url}/shipments`}>
						<ShipmentPage listing={this.state.listing} />
					</Route>
					<Route path={`${match.url}/payments`}>
						<PaymentsPage  listing={this.state.listing} />
					</Route>
					<Route path={`${match.url}/info`}>
						<ListingInfo listing={this.state.listing} />
					</Route>
					<Route path={`${match.url}`}>
						<Redirect to={{pathname: `${match.url}/info`, search: this.props.location.search}} />
					</Route>
				</Switch>
			</div>
		);
	}
}



class ListingInfo extends React.Component {
	render() {
		return <ul>
			<li>Gjaldmiðill: {this.props.listing.currency}</li>
			<li>Gengi (með afslætti og vsk breytingu): {this.props.listing.exchange_rate}</li>
			<li>Opnar: {this.props.listing.opens}</li>
			<li>Lokar: {this.props.listing.closes}</li>
		</ul>;
	}
}

class Listings extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			listings: null,
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token")
		};
	}

	componentDidMount() {
		fetch("/api/listings", {headers: {'Authorization': this.state.auth_token}})
			.then(res => res.json())
			.then(
				(results) => {this.setState(results)}
			);
	}

	render() {
		if (this.state.listings === null)
			return "";

		const {match} = this.props;
		
		const listings = this.state.listings.map((value, idx) => 
			<tr key={idx}>
				<td key="title"><Link to={{pathname: `${match.url}/listing/${value.id}`, search: this.props.location.search}}>{value.title}</Link></td>
				<td key="opens">{value.opens}</td>
				<td key="closes">{value.closes}</td>
				<td key="currency">{value.currency}</td>
				<td key="exchange_rate">{value.exchange_rate}</td>
			</tr>
		);
		return (
			<div>
				<h2 className="pt-5 mt-2">Pantanir</h2>
				<table className="table table-striped table-hover table-sm">
					<thead>
						<tr>
							<th key="title">Nafn pöntunar</th>
							<th key="opens">Opnar</th>
							<th key="closes">Lokar</th>
							<th key="currency">Gjaldmiðill</th>
							<th key="exchange_rate">Gengi</th>
						</tr>
					</thead>
					<tbody>{listings}</tbody>
				</table>
			</div>
		);
	}
}

ReactDOM.render(
	<Wrapper />,
	document.getElementById('root')
);
