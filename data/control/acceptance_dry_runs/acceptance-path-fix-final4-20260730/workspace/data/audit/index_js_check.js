
const DB = JSON.parse(document.getElementById('db').textContent);
const EQUAL_WEIGHT_TEST_RATINGS = {"Indiana":{"rating":31.102,"rank":1,"source_count":5,"missing_sources":""},"Ohio State":{"rating":30.152,"rank":2,"source_count":5,"missing_sources":""},"Notre Dame":{"rating":27.258,"rank":3,"source_count":5,"missing_sources":""},"Oregon":{"rating":26.582,"rank":4,"source_count":5,"missing_sources":""},"Texas Tech":{"rating":24.776,"rank":5,"source_count":5,"missing_sources":""},"Georgia":{"rating":23.172,"rank":6,"source_count":5,"missing_sources":""},"Miami-FL":{"rating":23.12,"rank":7,"source_count":5,"missing_sources":""},"Texas A&M":{"rating":20.362,"rank":8,"source_count":5,"missing_sources":""},"Texas":{"rating":20.014,"rank":9,"source_count":5,"missing_sources":""},"Alabama":{"rating":19.942,"rank":10,"source_count":5,"missing_sources":""},"Utah":{"rating":19.214,"rank":11,"source_count":5,"missing_sources":""},"Ole Miss":{"rating":19.154,"rank":12,"source_count":5,"missing_sources":""},"USC":{"rating":18.208,"rank":13,"source_count":5,"missing_sources":""},"Oklahoma":{"rating":17.61,"rank":14,"source_count":5,"missing_sources":""},"Penn State":{"rating":16.68,"rank":15,"source_count":5,"missing_sources":""},"Vanderbilt":{"rating":16.5,"rank":16,"source_count":5,"missing_sources":""},"Iowa":{"rating":16.352,"rank":17,"source_count":5,"missing_sources":""},"BYU":{"rating":15.488,"rank":18,"source_count":5,"missing_sources":""},"Michigan":{"rating":15.478,"rank":19,"source_count":5,"missing_sources":""},"Tennessee":{"rating":15.156,"rank":20,"source_count":5,"missing_sources":""},"Washington":{"rating":14.972,"rank":21,"source_count":5,"missing_sources":""},"Missouri":{"rating":14.534,"rank":22,"source_count":5,"missing_sources":""},"LSU":{"rating":13.312,"rank":23,"source_count":5,"missing_sources":""},"Auburn":{"rating":12.264,"rank":24,"source_count":5,"missing_sources":""},"SMU":{"rating":12.202,"rank":25,"source_count":5,"missing_sources":""},"Clemson":{"rating":11.332,"rank":26,"source_count":5,"missing_sources":""},"Arizona":{"rating":11.118,"rank":27,"source_count":5,"missing_sources":""},"Illinois":{"rating":11.092,"rank":28,"source_count":5,"missing_sources":""},"Florida":{"rating":10.954,"rank":29,"source_count":5,"missing_sources":""},"Louisville":{"rating":10.676,"rank":30,"source_count":5,"missing_sources":""},"Florida State":{"rating":10.306,"rank":31,"source_count":5,"missing_sources":""},"South Carolina":{"rating":10.168,"rank":32,"source_count":5,"missing_sources":""},"TCU":{"rating":9.908,"rank":33,"source_count":5,"missing_sources":""},"Kansas State":{"rating":8.794,"rank":34,"source_count":5,"missing_sources":""},"Pittsburgh":{"rating":8.488,"rank":35,"source_count":5,"missing_sources":""},"Virginia":{"rating":8.334,"rank":36,"source_count":5,"missing_sources":""},"South Florida":{"rating":8.068,"rank":37,"source_count":5,"missing_sources":""},"Georgia Tech":{"rating":8.024,"rank":38,"source_count":5,"missing_sources":""},"James Madison":{"rating":7.654,"rank":39,"source_count":5,"missing_sources":""},"Arkansas":{"rating":7.51,"rank":40,"source_count":5,"missing_sources":""},"Iowa State":{"rating":7.386,"rank":41,"source_count":5,"missing_sources":""},"Arizona State":{"rating":6.948,"rank":42,"source_count":5,"missing_sources":""},"Nebraska":{"rating":6.774,"rank":43,"source_count":5,"missing_sources":""},"Duke":{"rating":6.422,"rank":44,"source_count":5,"missing_sources":""},"Houston":{"rating":6.306,"rank":45,"source_count":5,"missing_sources":""},"Cincinnati":{"rating":5.562,"rank":46,"source_count":5,"missing_sources":""},"NC State":{"rating":5.292,"rank":47,"source_count":5,"missing_sources":""},"Mississippi State":{"rating":5.204,"rank":48,"source_count":5,"missing_sources":""},"Kentucky":{"rating":5.028,"rank":49,"source_count":5,"missing_sources":""},"Kansas":{"rating":4.99,"rank":50,"source_count":5,"missing_sources":""},"Boise State":{"rating":4.588,"rank":51,"source_count":5,"missing_sources":""},"Baylor":{"rating":4.58,"rank":52,"source_count":5,"missing_sources":""},"Northwestern":{"rating":4.568,"rank":53,"source_count":5,"missing_sources":""},"North Texas":{"rating":3.832,"rank":54,"source_count":5,"missing_sources":""},"Wake Forest":{"rating":3.408,"rank":55,"source_count":5,"missing_sources":""},"Wisconsin":{"rating":3.094,"rank":56,"source_count":5,"missing_sources":""},"East Carolina":{"rating":2.648,"rank":57,"source_count":5,"missing_sources":""},"Minnesota":{"rating":2.626,"rank":58,"source_count":5,"missing_sources":""},"Old Dominion":{"rating":2.536,"rank":59,"source_count":5,"missing_sources":""},"Rutgers":{"rating":2.372,"rank":60,"source_count":5,"missing_sources":""},"Tulane":{"rating":2.056,"rank":61,"source_count":5,"missing_sources":""},"Michigan State":{"rating":1.598,"rank":62,"source_count":5,"missing_sources":""},"Memphis":{"rating":1.478,"rank":63,"source_count":5,"missing_sources":""},"Navy":{"rating":1.252,"rank":64,"source_count":5,"missing_sources":""},"Virginia Tech":{"rating":0.898,"rank":65,"source_count":5,"missing_sources":""},"Toledo":{"rating":0.73,"rank":66,"source_count":5,"missing_sources":""},"Central Florida":{"rating":0.59,"rank":67,"source_count":5,"missing_sources":""},"UTSA":{"rating":0.07,"rank":68,"source_count":5,"missing_sources":""},"Maryland":{"rating":0.018,"rank":69,"source_count":5,"missing_sources":""},"UCLA":{"rating":-0.098,"rank":70,"source_count":5,"missing_sources":""},"UNLV":{"rating":-0.304,"rank":71,"source_count":5,"missing_sources":""},"San Diego State":{"rating":-0.374,"rank":72,"source_count":5,"missing_sources":""},"Washington State":{"rating":-0.476,"rank":73,"source_count":5,"missing_sources":""},"California":{"rating":-1.264,"rank":74,"source_count":5,"missing_sources":""},"North Dakota State":{"rating":-1.4,"rank":75,"source_count":1,"missing_sources":"fpi,teamrankings,kford,bradpowers"},"West Virginia":{"rating":-2.146,"rank":76,"source_count":5,"missing_sources":""},"Colorado":{"rating":-2.184,"rank":77,"source_count":5,"missing_sources":""},"New Mexico":{"rating":-2.552,"rank":78,"source_count":5,"missing_sources":""},"Texas State":{"rating":-2.996,"rank":79,"source_count":5,"missing_sources":""},"Army":{"rating":-3.074,"rank":80,"source_count":5,"missing_sources":""},"North Carolina":{"rating":-3.216,"rank":81,"source_count":5,"missing_sources":""},"Stanford":{"rating":-3.526,"rank":82,"source_count":5,"missing_sources":""},"Boston College":{"rating":-3.53,"rank":83,"source_count":5,"missing_sources":""},"Purdue":{"rating":-3.806,"rank":84,"source_count":5,"missing_sources":""},"Fresno State":{"rating":-3.852,"rank":85,"source_count":5,"missing_sources":""},"Hawaii":{"rating":-4.602,"rank":86,"source_count":5,"missing_sources":""},"Western Michigan":{"rating":-4.69,"rank":87,"source_count":5,"missing_sources":""},"Utah State":{"rating":-4.776,"rank":88,"source_count":5,"missing_sources":""},"Connecticut":{"rating":-4.868,"rank":89,"source_count":5,"missing_sources":""},"Ohio":{"rating":-5.632,"rank":90,"source_count":5,"missing_sources":""},"Miami-OH":{"rating":-6.468,"rank":91,"source_count":5,"missing_sources":""},"Syracuse":{"rating":-6.994,"rank":92,"source_count":5,"missing_sources":""},"Western Kentucky":{"rating":-7.058,"rank":93,"source_count":5,"missing_sources":""},"Air Force":{"rating":-7.424,"rank":94,"source_count":5,"missing_sources":""},"Marshall":{"rating":-7.578,"rank":95,"source_count":5,"missing_sources":""},"Louisiana Tech":{"rating":-7.684,"rank":96,"source_count":5,"missing_sources":""},"Oklahoma State":{"rating":-7.696,"rank":97,"source_count":5,"missing_sources":""},"Troy":{"rating":-7.916,"rank":98,"source_count":5,"missing_sources":""},"Kennesaw State":{"rating":-8.566,"rank":99,"source_count":5,"missing_sources":""},"Temple":{"rating":-9.052,"rank":100,"source_count":5,"missing_sources":""},"Liberty":{"rating":-9.778,"rank":101,"source_count":5,"missing_sources":""},"Jacksonville State":{"rating":-9.958,"rank":102,"source_count":5,"missing_sources":""},"Arkansas State":{"rating":-10.406,"rank":103,"source_count":5,"missing_sources":""},"Oregon State":{"rating":-10.642,"rank":104,"source_count":5,"missing_sources":""},"Georgia Southern":{"rating":-10.66,"rank":105,"source_count":5,"missing_sources":""},"Louisiana":{"rating":-10.868,"rank":106,"source_count":5,"missing_sources":""},"Florida Atlantic":{"rating":-11.172,"rank":107,"source_count":5,"missing_sources":""},"South Alabama":{"rating":-11.234,"rank":108,"source_count":5,"missing_sources":""},"Wyoming":{"rating":-11.392,"rank":109,"source_count":5,"missing_sources":""},"Central Michigan":{"rating":-11.682,"rank":110,"source_count":5,"missing_sources":""},"Florida International":{"rating":-11.956,"rank":111,"source_count":5,"missing_sources":""},"Southern Miss":{"rating":-11.992,"rank":112,"source_count":5,"missing_sources":""},"Tulsa":{"rating":-12.47,"rank":113,"source_count":5,"missing_sources":""},"Colorado State":{"rating":-13.156,"rank":114,"source_count":5,"missing_sources":""},"Buffalo":{"rating":-13.282,"rank":115,"source_count":5,"missing_sources":""},"Delaware":{"rating":-13.414,"rank":116,"source_count":5,"missing_sources":""},"Appalachian State":{"rating":-13.524,"rank":117,"source_count":5,"missing_sources":""},"Missouri State":{"rating":-13.81,"rank":118,"source_count":5,"missing_sources":""},"San Jose State":{"rating":-14.108,"rank":119,"source_count":5,"missing_sources":""},"Bowling Green":{"rating":-14.256,"rank":120,"source_count":5,"missing_sources":""},"Nevada":{"rating":-14.362,"rank":121,"source_count":5,"missing_sources":""},"Eastern Michigan":{"rating":-15.322,"rank":122,"source_count":5,"missing_sources":""},"Coastal Carolina":{"rating":-15.356,"rank":123,"source_count":5,"missing_sources":""},"UAB":{"rating":-16.224,"rank":124,"source_count":5,"missing_sources":""},"Northern Illinois":{"rating":-16.886,"rank":125,"source_count":5,"missing_sources":""},"Rice":{"rating":-17.12,"rank":126,"source_count":5,"missing_sources":""},"New Mexico State":{"rating":-17.748,"rank":127,"source_count":5,"missing_sources":""},"UTEP":{"rating":-18.516,"rank":128,"source_count":5,"missing_sources":""},"Akron":{"rating":-18.776,"rank":129,"source_count":5,"missing_sources":""},"Georgia State":{"rating":-20.096,"rank":130,"source_count":5,"missing_sources":""},"Middle Tennessee":{"rating":-20.204,"rank":131,"source_count":5,"missing_sources":""},"Kent State":{"rating":-20.446,"rank":132,"source_count":5,"missing_sources":""},"UL-Monroe":{"rating":-20.574,"rank":133,"source_count":5,"missing_sources":""},"Ball State":{"rating":-22.428,"rank":134,"source_count":5,"missing_sources":""},"Sacramento State":{"rating":-22.7,"rank":135,"source_count":1,"missing_sources":"fpi,teamrankings,kford,bradpowers"},"Charlotte":{"rating":-24.416,"rank":136,"source_count":5,"missing_sources":""},"Sam Houston":{"rating":-25.46,"rank":137,"source_count":5,"missing_sources":""},"Massachusetts":{"rating":-32.392,"rank":138,"source_count":5,"missing_sources":""}};
const RATING_SOURCE_VALUES = {"Air Force":{"spplus":-2.4,"fpi":-8.4,"teamrankings":-7.1,"kford":-8.1,"bradpowers":-11.1221},"Akron":{"spplus":-19.5,"fpi":-17.6,"teamrankings":-19.9,"kford":-19.6,"bradpowers":-17.2821},"Alabama":{"spplus":18.2,"fpi":19.0,"teamrankings":22.8,"kford":21.5,"bradpowers":18.2079},"Appalachian State":{"spplus":-12.1,"fpi":-13.3,"teamrankings":-14.9,"kford":-13.4,"bradpowers":-13.9221},"Arizona":{"spplus":10.2,"fpi":10.1,"teamrankings":12.7,"kford":11.2,"bradpowers":11.3879},"Arizona State":{"spplus":6.4,"fpi":6.3,"teamrankings":8.6,"kford":7.5,"bradpowers":5.9379},"Arkansas":{"spplus":5.0,"fpi":6.6,"teamrankings":8.6,"kford":7.8,"bradpowers":9.5479},"Arkansas State":{"spplus":-8.5,"fpi":-9.6,"teamrankings":-11.8,"kford":-11.7,"bradpowers":-10.4321},"Army":{"spplus":-3.0,"fpi":-2.7,"teamrankings":-2.2,"kford":-4.6,"bradpowers":-2.8721},"Auburn":{"spplus":11.2,"fpi":11.1,"teamrankings":13.3,"kford":12.0,"bradpowers":13.7179},"BYU":{"spplus":15.5,"fpi":15.3,"teamrankings":17.4,"kford":15.8,"bradpowers":13.4379},"Ball State":{"spplus":-25.2,"fpi":-19.4,"teamrankings":-22.2,"kford":-21.5,"bradpowers":-23.8421},"Baylor":{"spplus":4.5,"fpi":3.0,"teamrankings":5.6,"kford":4.1,"bradpowers":5.6979},"Boise State":{"spplus":6.8,"fpi":3.6,"teamrankings":4.3,"kford":4.9,"bradpowers":3.3379},"Boston College":{"spplus":-1.5,"fpi":-5.2,"teamrankings":-2.6,"kford":-4.8,"bradpowers":-3.5521},"Bowling Green":{"spplus":-13.3,"fpi":-11.8,"teamrankings":-15.0,"kford":-14.1,"bradpowers":-17.0821},"Buffalo":{"spplus":-11.9,"fpi":-13.3,"teamrankings":-13.2,"kford":-13.6,"bradpowers":-14.4121},"California":{"spplus":3.7,"fpi":-3.4,"teamrankings":-2.3,"kford":-3.3,"bradpowers":-1.0221},"Central Florida":{"spplus":2.3,"fpi":-0.8,"teamrankings":1.7,"kford":0.0,"bradpowers":-0.2521},"Central Michigan":{"spplus":-12.4,"fpi":-11.2,"teamrankings":-11.4,"kford":-11.5,"bradpowers":-11.9121},"Charlotte":{"spplus":-32.4,"fpi":-21.3,"teamrankings":-23.3,"kford":-22.7,"bradpowers":-22.3821},"Cincinnati":{"spplus":4.5,"fpi":3.7,"teamrankings":6.7,"kford":6.7,"bradpowers":6.2079},"Clemson":{"spplus":12.8,"fpi":9.5,"teamrankings":12.9,"kford":10.8,"bradpowers":10.6579},"Coastal Carolina":{"spplus":-13.8,"fpi":-14.2,"teamrankings":-15.7,"kford":-16.1,"bradpowers":-16.9821},"Colorado":{"spplus":0.9,"fpi":-2.7,"teamrankings":-2.0,"kford":-2.6,"bradpowers":-4.5221},"Colorado State":{"spplus":-8.3,"fpi":-13.2,"teamrankings":-13.6,"kford":-13.5,"bradpowers":-17.1821},"Connecticut":{"spplus":-11.2,"fpi":-3.5,"teamrankings":-3.7,"kford":-2.8,"bradpowers":-3.1421},"Delaware":{"spplus":-13.0,"fpi":-12.9,"teamrankings":-13.9,"kford":-14.3,"bradpowers":-12.9721},"Duke":{"spplus":5.7,"fpi":6.4,"teamrankings":7.5,"kford":5.9,"bradpowers":6.6079},"East Carolina":{"spplus":-2.0,"fpi":5.1,"teamrankings":4.9,"kford":3.2,"bradpowers":2.0379},"Eastern Michigan":{"spplus":-15.0,"fpi":-13.5,"teamrankings":-16.4,"kford":-15.7,"bradpowers":-16.0121},"Florida":{"spplus":14.9,"fpi":8.2,"teamrankings":11.7,"kford":9.5,"bradpowers":10.4679},"Florida Atlantic":{"spplus":-7.1,"fpi":-11.3,"teamrankings":-13.7,"kford":-12.8,"bradpowers":-10.9621},"Florida International":{"spplus":-13.7,"fpi":-11.2,"teamrankings":-12.3,"kford":-10.9,"bradpowers":-11.6821},"Florida State":{"spplus":8.8,"fpi":9.4,"teamrankings":13.3,"kford":10.8,"bradpowers":9.2279},"Fresno State":{"spplus":-2.3,"fpi":-4.3,"teamrankings":-2.5,"kford":-5.0,"bradpowers":-5.1621},"Georgia":{"spplus":25.5,"fpi":21.4,"teamrankings":23.6,"kford":22.5,"bradpowers":22.8579},"Georgia Southern":{"spplus":-8.9,"fpi":-9.7,"teamrankings":-11.1,"kford":-12.4,"bradpowers":-11.2021},"Georgia State":{"spplus":-25.1,"fpi":-17.6,"teamrankings":-20.2,"kford":-19.5,"bradpowers":-18.0821},"Georgia Tech":{"spplus":6.0,"fpi":7.6,"teamrankings":10.1,"kford":7.9,"bradpowers":8.5179},"Hawaii":{"spplus":-3.9,"fpi":-5.2,"teamrankings":-4.7,"kford":-5.7,"bradpowers":-3.5121},"Houston":{"spplus":8.2,"fpi":4.4,"teamrankings":6.6,"kford":4.7,"bradpowers":7.6279},"Illinois":{"spplus":9.3,"fpi":10.0,"teamrankings":13.6,"kford":11.0,"bradpowers":11.5579},"Indiana":{"spplus":24.5,"fpi":31.5,"teamrankings":36.3,"kford":30.7,"bradpowers":32.5079},"Iowa":{"spplus":13.6,"fpi":15.3,"teamrankings":20.0,"kford":16.4,"bradpowers":16.4579},"Iowa State":{"spplus":1.0,"fpi":8.6,"teamrankings":10.2,"kford":9.0,"bradpowers":8.1279},"Jacksonville State":{"spplus":-7.7,"fpi":-9.5,"teamrankings":-10.6,"kford":-11.2,"bradpowers":-10.7921},"James Madison":{"spplus":-2.1,"fpi":10.3,"teamrankings":10.8,"kford":9.6,"bradpowers":9.6679},"Kansas":{"spplus":3.7,"fpi":4.4,"teamrankings":6.3,"kford":5.5,"bradpowers":5.0479},"Kansas State":{"spplus":10.4,"fpi":7.8,"teamrankings":9.5,"kford":8.4,"bradpowers":7.8679},"Kennesaw State":{"spplus":-9.3,"fpi":-8.0,"teamrankings":-9.4,"kford":-7.1,"bradpowers":-9.0321},"Kent State":{"spplus":-20.1,"fpi":-19.6,"teamrankings":-21.3,"kford":-21.3,"bradpowers":-19.9321},"Kentucky":{"spplus":3.8,"fpi":5.1,"teamrankings":5.5,"kford":5.0,"bradpowers":5.7379},"LSU":{"spplus":20.2,"fpi":10.7,"teamrankings":13.5,"kford":12.4,"bradpowers":9.7579},"Liberty":{"spplus":-6.4,"fpi":-10.7,"teamrankings":-10.1,"kford":-10.4,"bradpowers":-11.2921},"Louisiana":{"spplus":-9.1,"fpi":-10.6,"teamrankings":-11.7,"kford":-11.2,"bradpowers":-11.7421},"Louisiana Tech":{"spplus":-8.3,"fpi":-6.2,"teamrankings":-6.7,"kford":-6.7,"bradpowers":-10.5221},"Louisville":{"spplus":11.0,"fpi":10.2,"teamrankings":12.0,"kford":10.7,"bradpowers":9.4779},"Marshall":{"spplus":-6.4,"fpi":-5.8,"teamrankings":-8.4,"kford":-8.0,"bradpowers":-9.2921},"Maryland":{"spplus":3.8,"fpi":-1.7,"teamrankings":0.0,"kford":-1.3,"bradpowers":-0.7121},"Massachusetts":{"spplus":-30.9,"fpi":-30.5,"teamrankings":-34.1,"kford":-32.8,"bradpowers":-33.6621},"Memphis":{"spplus":-1.1,"fpi":3.4,"teamrankings":2.0,"kford":3.6,"bradpowers":-0.5121},"Miami-FL":{"spplus":21.0,"fpi":22.4,"teamrankings":25.5,"kford":22.0,"bradpowers":24.6979},"Miami-OH":{"spplus":-2.9,"fpi":-5.7,"teamrankings":-7.0,"kford":-6.7,"bradpowers":-10.0421},"Michigan":{"spplus":16.1,"fpi":14.2,"teamrankings":16.6,"kford":15.9,"bradpowers":14.5879},"Michigan State":{"spplus":0.4,"fpi":0.8,"teamrankings":3.5,"kford":1.5,"bradpowers":1.7879},"Middle Tennessee":{"spplus":-26.0,"fpi":-18.0,"teamrankings":-19.7,"kford":-18.9,"bradpowers":-18.4221},"Minnesota":{"spplus":5.2,"fpi":1.1,"teamrankings":4.4,"kford":2.1,"bradpowers":0.3279},"Mississippi State":{"spplus":3.9,"fpi":3.4,"teamrankings":5.8,"kford":5.5,"bradpowers":7.4179},"Missouri":{"spplus":14.8,"fpi":13.1,"teamrankings":14.7,"kford":14.3,"bradpowers":15.7679},"Missouri State":{"spplus":-18.7,"fpi":-11.5,"teamrankings":-13.3,"kford":-12.4,"bradpowers":-13.1521},"NC State":{"spplus":4.9,"fpi":5.2,"teamrankings":7.9,"kford":4.6,"bradpowers":3.8579},"Navy":{"spplus":1.1,"fpi":0.5,"teamrankings":2.2,"kford":-0.6,"bradpowers":3.0579},"Nebraska":{"spplus":7.7,"fpi":5.5,"teamrankings":9.7,"kford":7.7,"bradpowers":3.2679},"Nevada":{"spplus":-12.2,"fpi":-14.3,"teamrankings":-15.4,"kford":-15.1,"bradpowers":-14.8121},"New Mexico":{"spplus":-0.5,"fpi":-2.7,"teamrankings":-3.9,"kford":-3.2,"bradpowers":-2.4621},"New Mexico State":{"spplus":-16.4,"fpi":-17.2,"teamrankings":-18.1,"kford":-17.9,"bradpowers":-19.1421},"North Carolina":{"spplus":3.8,"fpi":-5.9,"teamrankings":-4.7,"kford":-6.2,"bradpowers":-3.0821},"North Dakota State":{"spplus":-1.4,"fpi":null,"teamrankings":null,"kford":null,"bradpowers":null},"North Texas":{"spplus":-11.8,"fpi":7.0,"teamrankings":8.3,"kford":7.6,"bradpowers":8.0579},"Northern Illinois":{"spplus":-18.2,"fpi":-14.3,"teamrankings":-17.0,"kford":-16.2,"bradpowers":-18.7321},"Northwestern":{"spplus":4.6,"fpi":3.5,"teamrankings":5.8,"kford":3.6,"bradpowers":5.3379},"Notre Dame":{"spplus":25.8,"fpi":25.3,"teamrankings":29.8,"kford":27.0,"bradpowers":28.3879},"Ohio":{"spplus":-13.6,"fpi":-2.4,"teamrankings":-3.7,"kford":-4.5,"bradpowers":-3.9621},"Ohio State":{"spplus":31.8,"fpi":27.6,"teamrankings":32.1,"kford":30.0,"bradpowers":29.2579},"Oklahoma":{"spplus":17.2,"fpi":15.9,"teamrankings":19.1,"kford":18.1,"bradpowers":17.7479},"Oklahoma State":{"spplus":7.1,"fpi":-12.1,"teamrankings":-11.0,"kford":-12.2,"bradpowers":-10.2821},"Old Dominion":{"spplus":-5.8,"fpi":4.8,"teamrankings":4.7,"kford":3.0,"bradpowers":5.9779},"Ole Miss":{"spplus":15.9,"fpi":19.3,"teamrankings":21.7,"kford":18.9,"bradpowers":19.9679},"Oregon":{"spplus":28.3,"fpi":23.9,"teamrankings":28.6,"kford":26.5,"bradpowers":25.6079},"Oregon State":{"spplus":-6.3,"fpi":-11.6,"teamrankings":-11.3,"kford":-11.8,"bradpowers":-12.2121},"Penn State":{"spplus":15.7,"fpi":15.9,"teamrankings":19.5,"kford":16.9,"bradpowers":15.3979},"Pittsburgh":{"spplus":6.5,"fpi":7.7,"teamrankings":10.9,"kford":9.0,"bradpowers":8.3379},"Purdue":{"spplus":-2.9,"fpi":-4.7,"teamrankings":-3.2,"kford":-3.9,"bradpowers":-4.3321},"Rice":{"spplus":-14.7,"fpi":-17.3,"teamrankings":-18.9,"kford":-17.4,"bradpowers":-17.3021},"Rutgers":{"spplus":1.8,"fpi":1.5,"teamrankings":4.5,"kford":2.3,"bradpowers":1.7579},"SMU":{"spplus":10.9,"fpi":12.5,"teamrankings":13.9,"kford":12.1,"bradpowers":11.6079},"Sacramento State":{"spplus":-22.7,"fpi":null,"teamrankings":null,"kford":null,"bradpowers":null},"Sam Houston":{"spplus":-26.3,"fpi":-24.3,"teamrankings":-25.8,"kford":-25.2,"bradpowers":-25.7021},"San Diego State":{"spplus":-1.3,"fpi":0.6,"teamrankings":0.4,"kford":-0.5,"bradpowers":-1.0721},"San Jose State":{"spplus":-15.5,"fpi":-13.7,"teamrankings":-14.6,"kford":-13.8,"bradpowers":-12.9421},"South Alabama":{"spplus":-13.3,"fpi":-10.7,"teamrankings":-11.7,"kford":-11.2,"bradpowers":-9.2721},"South Carolina":{"spplus":12.1,"fpi":9.0,"teamrankings":10.5,"kford":9.1,"bradpowers":10.1379},"South Florida":{"spplus":-2.8,"fpi":11.1,"teamrankings":11.2,"kford":11.7,"bradpowers":9.1379},"Southern Miss":{"spplus":-23.3,"fpi":-8.6,"teamrankings":-10.4,"kford":-9.0,"bradpowers":-8.6621},"Stanford":{"spplus":-1.9,"fpi":-3.7,"teamrankings":-3.3,"kford":-4.9,"bradpowers":-3.8321},"Syracuse":{"spplus":-0.7,"fpi":-9.3,"teamrankings":-6.0,"kford":-8.2,"bradpowers":-10.7721},"TCU":{"spplus":9.1,"fpi":9.4,"teamrankings":10.3,"kford":9.0,"bradpowers":11.7379},"Temple":{"spplus":-8.7,"fpi":-8.4,"teamrankings":-8.7,"kford":-9.6,"bradpowers":-9.8621},"Tennessee":{"spplus":16.0,"fpi":14.3,"teamrankings":15.4,"kford":14.9,"bradpowers":15.1779},"Texas":{"spplus":23.7,"fpi":18.6,"teamrankings":19.6,"kford":18.0,"bradpowers":20.1679},"Texas A&M":{"spplus":20.3,"fpi":18.4,"teamrankings":21.4,"kford":20.2,"bradpowers":21.5079},"Texas State":{"spplus":-5.9,"fpi":-1.5,"teamrankings":-2.8,"kford":-3.6,"bradpowers":-1.1821},"Texas Tech":{"spplus":23.1,"fpi":21.5,"teamrankings":28.0,"kford":25.7,"bradpowers":25.5779},"Toledo":{"spplus":-11.5,"fpi":4.3,"teamrankings":5.2,"kford":3.5,"bradpowers":2.1479},"Troy":{"spplus":-6.0,"fpi":-6.8,"teamrankings":-8.4,"kford":-8.0,"bradpowers":-10.3821},"Tulane":{"spplus":-5.5,"fpi":3.7,"teamrankings":3.6,"kford":3.7,"bradpowers":4.7779},"Tulsa":{"spplus":-7.6,"fpi":-14.0,"teamrankings":-14.5,"kford":-14.8,"bradpowers":-11.4521},"UAB":{"spplus":-18.1,"fpi":-14.9,"teamrankings":-16.6,"kford":-16.1,"bradpowers":-15.4221},"UCLA":{"spplus":5.1,"fpi":-2.4,"teamrankings":0.0,"kford":-1.5,"bradpowers":-1.6921},"UL-Monroe":{"spplus":-24.3,"fpi":-19.2,"teamrankings":-21.2,"kford":-20.5,"bradpowers":-17.6721},"UNLV":{"spplus":2.8,"fpi":0.1,"teamrankings":-1.4,"kford":-0.6,"bradpowers":-2.4221},"USC":{"spplus":16.8,"fpi":18.0,"teamrankings":19.9,"kford":19.2,"bradpowers":17.1379},"UTEP":{"spplus":-20.5,"fpi":-16.6,"teamrankings":-18.9,"kford":-17.9,"bradpowers":-18.6821},"UTSA":{"spplus":-1.5,"fpi":1.6,"teamrankings":1.7,"kford":-0.6,"bradpowers":-0.8521},"Utah":{"spplus":11.9,"fpi":20.1,"teamrankings":24.0,"kford":21.1,"bradpowers":18.9679},"Utah State":{"spplus":-7.7,"fpi":-3.0,"teamrankings":-4.3,"kford":-3.6,"bradpowers":-5.2821},"Vanderbilt":{"spplus":10.0,"fpi":17.0,"teamrankings":19.2,"kford":17.8,"bradpowers":18.4979},"Virginia":{"spplus":6.6,"fpi":8.2,"teamrankings":9.8,"kford":7.5,"bradpowers":9.5679},"Virginia Tech":{"spplus":9.4,"fpi":-1.2,"teamrankings":-0.9,"kford":-1.8,"bradpowers":-1.0121},"Wake Forest":{"spplus":3.6,"fpi":2.1,"teamrankings":3.8,"kford":1.3,"bradpowers":6.2379},"Washington":{"spplus":14.5,"fpi":14.0,"teamrankings":17.9,"kford":14.6,"bradpowers":13.8579},"Washington State":{"spplus":-5.3,"fpi":1.4,"teamrankings":1.1,"kford":0.0,"bradpowers":0.4179},"West Virginia":{"spplus":0.8,"fpi":-4.1,"teamrankings":-1.8,"kford":-3.5,"bradpowers":-2.1321},"Western Kentucky":{"spplus":-5.3,"fpi":-7.4,"teamrankings":-6.4,"kford":-7.9,"bradpowers":-8.2921},"Western Michigan":{"spplus":-7.2,"fpi":-2.7,"teamrankings":-3.9,"kford":-6.1,"bradpowers":-3.5521},"Wisconsin":{"spplus":1.8,"fpi":2.5,"teamrankings":5.2,"kford":3.3,"bradpowers":2.6679},"Wyoming":{"spplus":-9.6,"fpi":-11.5,"teamrankings":-11.5,"kford":-11.8,"bradpowers":-12.5621}};
const RATING_SOURCE_STATUS = {"spplus":{"label":"SP+","file":"data/ratings/spplus_2026_from_espn_latest.csv","rows":138,"updated":"2026-04-29 09:01 PM","default_weight":1.0,"status":"live"},"fpi":{"label":"FPI","file":"data/ratings/fpi_2025_test_latest.csv","rows":136,"updated":"2026-04-29 09:01 PM","default_weight":0.0,"status":"test/stale"},"teamrankings":{"label":"TeamRankings","file":"data/ratings/teamrankings_2025_test_latest.csv","rows":136,"updated":"2026-04-29 09:01 PM","default_weight":0.0,"status":"test/stale"},"kford":{"label":"KFord","file":"data/ratings/kford_2025_test_latest.csv","rows":136,"updated":"2026-04-29 09:01 PM","default_weight":0.0,"status":"test/stale"},"bradpowers":{"label":"Brad Powers","file":"data/ratings/bradpowers_2025_test_latest.csv","rows":136,"updated":"2026-04-29 09:01 PM","default_weight":0.0,"status":"test/stale"}};
const DEFAULT_RATING_WEIGHTS = {"spplus":1.0,"fpi":0.0,"teamrankings":0.0,"kford":0.0,"bradpowers":0.0};
const teamBySlug = Object.fromEntries(DB.teams.map(t => [t.slug, t]));
const teamByName = Object.fromEntries(DB.teams.map(t => [t.team.toLowerCase(), t]));
const RATING_TRENDS = {"Ohio State":{"rating_2026_current":31.8,"rank_2026_current":1,"rating_2025_eoy":29.811588235294117,"rank_2025_eoy":2,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.9884117647058837,"rank_trend":1},"Oregon":{"rating_2026_current":28.3,"rank_2026_current":2,"rating_2025_eoy":26.101588235294116,"rank_2025_eoy":4,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.1984117647058845,"rank_trend":2},"Notre Dame":{"rating_2026_current":25.8,"rank_2026_current":3,"rating_2025_eoy":26.97758823529411,"rank_2025_eoy":3,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.1775882352941096,"rank_trend":0},"Georgia":{"rating_2026_current":25.5,"rank_2026_current":4,"rating_2025_eoy":22.891588235294115,"rank_2025_eoy":7,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.6084117647058847,"rank_trend":3},"Indiana":{"rating_2026_current":24.5,"rank_2026_current":5,"rating_2025_eoy":32.681588235294114,"rank_2025_eoy":1,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-8.181588235294114,"rank_trend":-4},"Texas":{"rating_2026_current":23.7,"rank_2026_current":6,"rating_2025_eoy":18.51358823529412,"rank_2025_eoy":13,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":5.1864117647058805,"rank_trend":7},"Texas Tech":{"rating_2026_current":23.1,"rank_2026_current":7,"rating_2025_eoy":25.67558823529412,"rank_2025_eoy":5,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.57558823529412,"rank_trend":-2},"Miami-FL":{"rating_2026_current":21.0,"rank_2026_current":8,"rating_2025_eoy":23.05958823529412,"rank_2025_eoy":6,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.0595882352941217,"rank_trend":-2},"Texas A&M":{"rating_2026_current":20.3,"rank_2026_current":9,"rating_2025_eoy":20.441588235294116,"rank_2025_eoy":10,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.1415882352941153,"rank_trend":1},"LSU":{"rating_2026_current":20.2,"rank_2026_current":10,"rating_2025_eoy":11.331588235294118,"rank_2025_eoy":27,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":8.86841176470588,"rank_trend":17},"Alabama":{"rating_2026_current":18.2,"rank_2026_current":11,"rating_2025_eoy":19.261588235294116,"rank_2025_eoy":11,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.061588235294117,"rank_trend":0},"Oklahoma":{"rating_2026_current":17.2,"rank_2026_current":12,"rating_2025_eoy":17.829588235294118,"rank_2025_eoy":15,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.6295882352941184,"rank_trend":3},"USC":{"rating_2026_current":16.8,"rank_2026_current":13,"rating_2025_eoy":18.227588235294117,"rank_2025_eoy":14,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.4275882352941167,"rank_trend":1},"Michigan":{"rating_2026_current":16.1,"rank_2026_current":14,"rating_2025_eoy":14.737588235294115,"rank_2025_eoy":21,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.362411764705886,"rank_trend":7},"Tennessee":{"rating_2026_current":16.0,"rank_2026_current":15,"rating_2025_eoy":14.95558823529412,"rank_2025_eoy":20,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.0444117647058793,"rank_trend":5},"Ole Miss":{"rating_2026_current":15.9,"rank_2026_current":16,"rating_2025_eoy":20.77358823529412,"rank_2025_eoy":9,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-4.87358823529412,"rank_trend":-7},"Penn State":{"rating_2026_current":15.7,"rank_2026_current":17,"rating_2025_eoy":17.15958823529412,"rank_2025_eoy":17,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.4595882352941203,"rank_trend":0},"BYU":{"rating_2026_current":15.5,"rank_2026_current":18,"rating_2025_eoy":15.56758823529412,"rank_2025_eoy":19,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.0675882352941208,"rank_trend":1},"Florida":{"rating_2026_current":14.9,"rank_2026_current":19,"rating_2025_eoy":8.673588235294117,"rank_2025_eoy":40,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":6.226411764705883,"rank_trend":21},"Missouri":{"rating_2026_current":14.8,"rank_2026_current":20,"rating_2025_eoy":14.453588235294117,"rank_2025_eoy":22,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":0.3464117647058842,"rank_trend":2},"Washington":{"rating_2026_current":14.5,"rank_2026_current":21,"rating_2025_eoy":15.751588235294117,"rank_2025_eoy":18,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.2515882352941166,"rank_trend":-3},"Iowa":{"rating_2026_current":13.6,"rank_2026_current":22,"rating_2025_eoy":17.57158823529412,"rank_2025_eoy":16,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-3.971588235294119,"rank_trend":-6},"Clemson":{"rating_2026_current":12.8,"rank_2026_current":23,"rating_2025_eoy":10.671588235294118,"rank_2025_eoy":30,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.1284117647058824,"rank_trend":7},"South Carolina":{"rating_2026_current":12.1,"rank_2026_current":24,"rating_2025_eoy":8.927588235294118,"rank_2025_eoy":37,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":3.172411764705881,"rank_trend":13},"Utah":{"rating_2026_current":11.9,"rank_2026_current":25,"rating_2025_eoy":21.27358823529412,"rank_2025_eoy":8,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-9.37358823529412,"rank_trend":-17},"Auburn":{"rating_2026_current":11.2,"rank_2026_current":26,"rating_2025_eoy":12.343588235294115,"rank_2025_eoy":24,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.143588235294116,"rank_trend":-2},"Louisville":{"rating_2026_current":11.0,"rank_2026_current":27,"rating_2025_eoy":10.95558823529412,"rank_2025_eoy":28,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":0.0444117647058792,"rank_trend":1},"SMU":{"rating_2026_current":10.9,"rank_2026_current":28,"rating_2025_eoy":12.701588235294118,"rank_2025_eoy":23,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.8015882352941173,"rank_trend":-5},"Kansas State":{"rating_2026_current":10.4,"rank_2026_current":29,"rating_2025_eoy":8.11358823529412,"rank_2025_eoy":41,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.28641176470588,"rank_trend":12},"Arizona":{"rating_2026_current":10.2,"rank_2026_current":30,"rating_2025_eoy":11.477588235294116,"rank_2025_eoy":26,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.2775882352941164,"rank_trend":-4},"Vanderbilt":{"rating_2026_current":10.0,"rank_2026_current":31,"rating_2025_eoy":18.55958823529412,"rank_2025_eoy":12,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-8.559588235294122,"rank_trend":-19},"Virginia Tech":{"rating_2026_current":9.4,"rank_2026_current":32,"rating_2025_eoy":-3.0024117647058817,"rank_2025_eoy":78,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":12.402411764705882,"rank_trend":46},"Illinois":{"rating_2026_current":9.3,"rank_2026_current":33,"rating_2025_eoy":11.81158823529412,"rank_2025_eoy":25,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.51158823529412,"rank_trend":-8},"TCU":{"rating_2026_current":9.1,"rank_2026_current":34,"rating_2025_eoy":9.747588235294115,"rank_2025_eoy":33,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.6475882352941156,"rank_trend":-1},"Florida State":{"rating_2026_current":8.8,"rank_2026_current":35,"rating_2025_eoy":9.98558823529412,"rank_2025_eoy":32,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.1855882352941194,"rank_trend":-3},"Houston":{"rating_2026_current":8.2,"rank_2026_current":36,"rating_2025_eoy":6.145588235294117,"rank_2025_eoy":46,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.0544117647058826,"rank_trend":10},"Nebraska":{"rating_2026_current":7.7,"rank_2026_current":37,"rating_2025_eoy":6.473588235294116,"rank_2025_eoy":44,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.226411764705884,"rank_trend":7},"Oklahoma State":{"rating_2026_current":7.1,"rank_2026_current":38,"rating_2025_eoy":-12.136411764705883,"rank_2025_eoy":110,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":19.236411764705885,"rank_trend":72},"Boise State":{"rating_2026_current":6.8,"rank_2026_current":39,"rating_2025_eoy":3.8475882352941184,"rank_2025_eoy":58,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.9524117647058814,"rank_trend":19},"Virginia":{"rating_2026_current":6.6,"rank_2026_current":40,"rating_2025_eoy":9.233588235294116,"rank_2025_eoy":34,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.633588235294116,"rank_trend":-6},"Pittsburgh":{"rating_2026_current":6.5,"rank_2026_current":41,"rating_2025_eoy":8.867588235294118,"rank_2025_eoy":38,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.367588235294118,"rank_trend":-3},"Arizona State":{"rating_2026_current":6.4,"rank_2026_current":42,"rating_2025_eoy":6.447588235294117,"rank_2025_eoy":45,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.0475882352941168,"rank_trend":3},"Georgia Tech":{"rating_2026_current":6.0,"rank_2026_current":43,"rating_2025_eoy":8.683588235294117,"rank_2025_eoy":39,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.683588235294117,"rank_trend":-4},"Duke":{"rating_2026_current":5.7,"rank_2026_current":44,"rating_2025_eoy":6.601588235294118,"rank_2025_eoy":43,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.9015882352941178,"rank_trend":-1},"Minnesota":{"rating_2026_current":5.2,"rank_2026_current":45,"rating_2025_eoy":1.8855882352941176,"rank_2025_eoy":63,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":3.3144117647058824,"rank_trend":18},"UCLA":{"rating_2026_current":5.1,"rank_2026_current":46,"rating_2025_eoy":-2.8584117647058815,"rank_2025_eoy":77,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":7.958411764705881,"rank_trend":31},"Arkansas":{"rating_2026_current":5.0,"rank_2026_current":47,"rating_2025_eoy":7.529588235294116,"rank_2025_eoy":42,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.529588235294116,"rank_trend":-5},"NC State":{"rating_2026_current":4.9,"rank_2026_current":48,"rating_2025_eoy":5.271588235294118,"rank_2025_eoy":48,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.3715882352941175,"rank_trend":0},"Northwestern":{"rating_2026_current":4.6,"rank_2026_current":49,"rating_2025_eoy":4.807588235294119,"rank_2025_eoy":52,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.2075882352941196,"rank_trend":3},"Baylor":{"rating_2026_current":4.5,"rank_2026_current":50,"rating_2025_eoy":3.959588235294119,"rank_2025_eoy":57,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":0.540411764705881,"rank_trend":7},"Cincinnati":{"rating_2026_current":4.5,"rank_2026_current":50,"rating_2025_eoy":5.561588235294116,"rank_2025_eoy":47,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.0615882352941162,"rank_trend":-3},"Mississippi State":{"rating_2026_current":3.9,"rank_2026_current":52,"rating_2025_eoy":5.243588235294118,"rank_2025_eoy":49,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.3435882352941184,"rank_trend":-3},"Maryland":{"rating_2026_current":3.8,"rank_2026_current":53,"rating_2025_eoy":-0.6224117647058822,"rank_2025_eoy":71,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":4.422411764705882,"rank_trend":18},"North Carolina":{"rating_2026_current":3.8,"rank_2026_current":53,"rating_2025_eoy":-5.296411764705882,"rank_2025_eoy":88,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":9.09641176470588,"rank_trend":35},"Kentucky":{"rating_2026_current":3.8,"rank_2026_current":53,"rating_2025_eoy":4.627588235294117,"rank_2025_eoy":54,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.8275882352941171,"rank_trend":1},"Kansas":{"rating_2026_current":3.7,"rank_2026_current":56,"rating_2025_eoy":5.069588235294118,"rank_2025_eoy":50,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.3695882352941178,"rank_trend":-6},"California":{"rating_2026_current":3.7,"rank_2026_current":56,"rating_2025_eoy":-2.6444117647058825,"rank_2025_eoy":76,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":6.344411764705883,"rank_trend":20},"Wake Forest":{"rating_2026_current":3.6,"rank_2026_current":58,"rating_2025_eoy":3.8275882352941175,"rank_2025_eoy":59,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.2275882352941174,"rank_trend":1},"UNLV":{"rating_2026_current":2.8,"rank_2026_current":59,"rating_2025_eoy":-0.0044117647058824,"rank_2025_eoy":69,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.804411764705882,"rank_trend":10},"Central Florida":{"rating_2026_current":2.3,"rank_2026_current":60,"rating_2025_eoy":-0.1104117647058819,"rank_2025_eoy":70,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.4104117647058816,"rank_trend":10},"Rutgers":{"rating_2026_current":1.8,"rank_2026_current":61,"rating_2025_eoy":2.211588235294119,"rank_2025_eoy":62,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.4115882352941191,"rank_trend":1},"Wisconsin":{"rating_2026_current":1.8,"rank_2026_current":61,"rating_2025_eoy":1.8535882352941184,"rank_2025_eoy":64,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.0535882352941183,"rank_trend":3},"Navy":{"rating_2026_current":1.1,"rank_2026_current":63,"rating_2025_eoy":2.271588235294119,"rank_2025_eoy":61,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.1715882352941187,"rank_trend":-2},"Iowa State":{"rating_2026_current":1.0,"rank_2026_current":64,"rating_2025_eoy":9.165588235294118,"rank_2025_eoy":35,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-8.165588235294118,"rank_trend":-29},"Colorado":{"rating_2026_current":0.9,"rank_2026_current":65,"rating_2025_eoy":-4.024411764705883,"rank_2025_eoy":85,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":4.924411764705884,"rank_trend":20},"West Virginia":{"rating_2026_current":0.8,"rank_2026_current":66,"rating_2025_eoy":-3.6664117647058823,"rank_2025_eoy":82,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":4.4664117647058825,"rank_trend":16},"Michigan State":{"rating_2026_current":0.4,"rank_2026_current":67,"rating_2025_eoy":0.8375882352941193,"rank_2025_eoy":68,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.4375882352941193,"rank_trend":1},"New Mexico":{"rating_2026_current":-0.5,"rank_2026_current":68,"rating_2025_eoy":-2.272411764705882,"rank_2025_eoy":74,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.772411764705882,"rank_trend":6},"Syracuse":{"rating_2026_current":-0.7,"rank_2026_current":69,"rating_2025_eoy":-9.47441176470588,"rank_2025_eoy":99,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":8.774411764705881,"rank_trend":30},"Memphis":{"rating_2026_current":-1.1,"rank_2026_current":70,"rating_2025_eoy":3.2175882352941185,"rank_2025_eoy":60,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-4.317588235294119,"rank_trend":-10},"San Diego State":{"rating_2026_current":-1.3,"rank_2026_current":71,"rating_2025_eoy":1.225588235294118,"rank_2025_eoy":66,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.5255882352941184,"rank_trend":-5},"North Dakota State":{"rating_2026_current":-1.4,"rank_2026_current":72,"rating_2025_eoy":null,"rank_2025_eoy":null,"source_count_2025":0,"missing_sources_2025":"spplus_2025,fpi_2025,teamrankings_2025,kford_2025,bradpowers_2025","rating_trend":null,"rank_trend":null},"UTSA":{"rating_2026_current":-1.5,"rank_2026_current":73,"rating_2025_eoy":1.109588235294118,"rank_2025_eoy":67,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.609588235294118,"rank_trend":-6},"Boston College":{"rating_2026_current":-1.5,"rank_2026_current":73,"rating_2025_eoy":-4.930411764705882,"rank_2025_eoy":87,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":3.430411764705882,"rank_trend":14},"Stanford":{"rating_2026_current":-1.9,"rank_2026_current":75,"rating_2025_eoy":-5.506411764705883,"rank_2025_eoy":89,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":3.606411764705882,"rank_trend":14},"East Carolina":{"rating_2026_current":-2.0,"rank_2026_current":76,"rating_2025_eoy":4.647588235294119,"rank_2025_eoy":53,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-6.647588235294119,"rank_trend":-23},"James Madison":{"rating_2026_current":-2.1,"rank_2026_current":77,"rating_2025_eoy":10.53358823529412,"rank_2025_eoy":31,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-12.63358823529412,"rank_trend":-46},"Fresno State":{"rating_2026_current":-2.3,"rank_2026_current":78,"rating_2025_eoy":-3.032411764705883,"rank_2025_eoy":79,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":0.732411764705883,"rank_trend":1},"Air Force":{"rating_2026_current":-2.4,"rank_2026_current":79,"rating_2025_eoy":-7.584411764705882,"rank_2025_eoy":94,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":5.184411764705882,"rank_trend":15},"South Florida":{"rating_2026_current":-2.8,"rank_2026_current":80,"rating_2025_eoy":10.947588235294116,"rank_2025_eoy":29,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-13.747588235294115,"rank_trend":-51},"Miami-OH":{"rating_2026_current":-2.9,"rank_2026_current":81,"rating_2025_eoy":-6.568411764705881,"rank_2025_eoy":92,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":3.668411764705881,"rank_trend":11},"Purdue":{"rating_2026_current":-2.9,"rank_2026_current":81,"rating_2025_eoy":-4.446411764705881,"rank_2025_eoy":86,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.5464117647058813,"rank_trend":5},"Army":{"rating_2026_current":-3.0,"rank_2026_current":83,"rating_2025_eoy":-2.3144117647058815,"rank_2025_eoy":75,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.6855882352941185,"rank_trend":-8},"Hawaii":{"rating_2026_current":-3.9,"rank_2026_current":84,"rating_2025_eoy":-3.482411764705881,"rank_2025_eoy":80,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.4175882352941187,"rank_trend":-4},"Western Kentucky":{"rating_2026_current":-5.3,"rank_2026_current":85,"rating_2025_eoy":-5.678411764705882,"rank_2025_eoy":90,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":0.3784117647058824,"rank_trend":5},"Washington State":{"rating_2026_current":-5.3,"rank_2026_current":85,"rating_2025_eoy":1.3435882352941182,"rank_2025_eoy":65,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-6.643588235294118,"rank_trend":-20},"Tulane":{"rating_2026_current":-5.5,"rank_2026_current":87,"rating_2025_eoy":4.415588235294118,"rank_2025_eoy":55,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-9.915588235294118,"rank_trend":-32},"Old Dominion":{"rating_2026_current":-5.8,"rank_2026_current":88,"rating_2025_eoy":4.875588235294119,"rank_2025_eoy":51,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-10.675588235294118,"rank_trend":-37},"Texas State":{"rating_2026_current":-5.9,"rank_2026_current":89,"rating_2025_eoy":-1.3564117647058818,"rank_2025_eoy":72,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-4.543588235294118,"rank_trend":-17},"Troy":{"rating_2026_current":-6.0,"rank_2026_current":90,"rating_2025_eoy":-7.676411764705883,"rank_2025_eoy":95,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.6764117647058834,"rank_trend":5},"Oregon State":{"rating_2026_current":-6.3,"rank_2026_current":91,"rating_2025_eoy":-12.562411764705882,"rank_2025_eoy":113,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":6.262411764705882,"rank_trend":22},"Marshall":{"rating_2026_current":-6.4,"rank_2026_current":92,"rating_2025_eoy":-7.198411764705883,"rank_2025_eoy":93,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":0.7984117647058824,"rank_trend":1},"Liberty":{"rating_2026_current":-6.4,"rank_2026_current":92,"rating_2025_eoy":-10.29841176470588,"rank_2025_eoy":101,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":3.89841176470588,"rank_trend":9},"Florida Atlantic":{"rating_2026_current":-7.1,"rank_2026_current":94,"rating_2025_eoy":-11.49241176470588,"rank_2025_eoy":108,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":4.39241176470588,"rank_trend":14},"Western Michigan":{"rating_2026_current":-7.2,"rank_2026_current":95,"rating_2025_eoy":-3.5304117647058817,"rank_2025_eoy":81,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-3.6695882352941185,"rank_trend":-14},"Tulsa":{"rating_2026_current":-7.6,"rank_2026_current":96,"rating_2025_eoy":-12.950411764705882,"rank_2025_eoy":114,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":5.350411764705882,"rank_trend":18},"Utah State":{"rating_2026_current":-7.7,"rank_2026_current":97,"rating_2025_eoy":-3.856411764705882,"rank_2025_eoy":84,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-3.843588235294118,"rank_trend":-13},"Jacksonville State":{"rating_2026_current":-7.7,"rank_2026_current":97,"rating_2025_eoy":-9.75841176470588,"rank_2025_eoy":100,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.0584117647058795,"rank_trend":3},"Colorado State":{"rating_2026_current":-8.3,"rank_2026_current":99,"rating_2025_eoy":-14.616411764705882,"rank_2025_eoy":120,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":6.316411764705881,"rank_trend":21},"Louisiana Tech":{"rating_2026_current":-8.3,"rank_2026_current":99,"rating_2025_eoy":-6.284411764705882,"rank_2025_eoy":91,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.0155882352941186,"rank_trend":-8},"Arkansas State":{"rating_2026_current":-8.5,"rank_2026_current":101,"rating_2025_eoy":-10.466411764705882,"rank_2025_eoy":102,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.9664117647058816,"rank_trend":1},"Temple":{"rating_2026_current":-8.7,"rank_2026_current":102,"rating_2025_eoy":-8.332411764705881,"rank_2025_eoy":97,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.367588235294118,"rank_trend":-5},"Georgia Southern":{"rating_2026_current":-8.9,"rank_2026_current":103,"rating_2025_eoy":-10.760411764705882,"rank_2025_eoy":103,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.8604117647058815,"rank_trend":0},"Louisiana":{"rating_2026_current":-9.1,"rank_2026_current":104,"rating_2025_eoy":-11.068411764705882,"rank_2025_eoy":105,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.9684117647058823,"rank_trend":1},"Kennesaw State":{"rating_2026_current":-9.3,"rank_2026_current":105,"rating_2025_eoy":-7.786411764705882,"rank_2025_eoy":96,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.5135882352941188,"rank_trend":-9},"Wyoming":{"rating_2026_current":-9.6,"rank_2026_current":106,"rating_2025_eoy":-11.732411764705882,"rank_2025_eoy":109,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.132411764705882,"rank_trend":3},"Connecticut":{"rating_2026_current":-11.2,"rank_2026_current":107,"rating_2025_eoy":-1.6084117647058822,"rank_2025_eoy":73,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-9.591588235294116,"rank_trend":-34},"Toledo":{"rating_2026_current":-11.5,"rank_2026_current":108,"rating_2025_eoy":4.229588235294119,"rank_2025_eoy":56,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-15.72958823529412,"rank_trend":-52},"North Texas":{"rating_2026_current":-11.8,"rank_2026_current":109,"rating_2025_eoy":8.95158823529412,"rank_2025_eoy":36,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-20.75158823529412,"rank_trend":-73},"Buffalo":{"rating_2026_current":-11.9,"rank_2026_current":110,"rating_2025_eoy":-12.402411764705883,"rank_2025_eoy":112,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":0.502411764705883,"rank_trend":2},"Appalachian State":{"rating_2026_current":-12.1,"rank_2026_current":111,"rating_2025_eoy":-13.384411764705884,"rank_2025_eoy":116,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.2844117647058848,"rank_trend":5},"Nevada":{"rating_2026_current":-12.2,"rank_2026_current":112,"rating_2025_eoy":-14.602411764705884,"rank_2025_eoy":119,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.402411764705885,"rank_trend":7},"Central Michigan":{"rating_2026_current":-12.4,"rank_2026_current":113,"rating_2025_eoy":-10.962411764705882,"rank_2025_eoy":104,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.4375882352941185,"rank_trend":-9},"Delaware":{"rating_2026_current":-13.0,"rank_2026_current":114,"rating_2025_eoy":-12.994411764705882,"rank_2025_eoy":115,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.0055882352941178,"rank_trend":1},"South Alabama":{"rating_2026_current":-13.3,"rank_2026_current":115,"rating_2025_eoy":-11.11441176470588,"rank_2025_eoy":106,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.185588235294121,"rank_trend":-9},"Bowling Green":{"rating_2026_current":-13.3,"rank_2026_current":115,"rating_2025_eoy":-14.116411764705882,"rank_2025_eoy":118,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":0.8164117647058813,"rank_trend":3},"Ohio":{"rating_2026_current":-13.6,"rank_2026_current":117,"rating_2025_eoy":-3.7124117647058825,"rank_2025_eoy":83,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-9.887588235294118,"rank_trend":-34},"Florida International":{"rating_2026_current":-13.7,"rank_2026_current":118,"rating_2025_eoy":-11.31641176470588,"rank_2025_eoy":107,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.38358823529412,"rank_trend":-11},"Coastal Carolina":{"rating_2026_current":-13.8,"rank_2026_current":119,"rating_2025_eoy":-15.616411764705884,"rank_2025_eoy":122,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.816411764705883,"rank_trend":3},"Rice":{"rating_2026_current":-14.7,"rank_2026_current":120,"rating_2025_eoy":-17.14041176470588,"rank_2025_eoy":125,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.440411764705882,"rank_trend":5},"Eastern Michigan":{"rating_2026_current":-15.0,"rank_2026_current":121,"rating_2025_eoy":-15.262411764705885,"rank_2025_eoy":121,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":0.2624117647058845,"rank_trend":0},"San Jose State":{"rating_2026_current":-15.5,"rank_2026_current":122,"rating_2025_eoy":-13.868411764705884,"rank_2025_eoy":117,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.6315882352941156,"rank_trend":-5},"New Mexico State":{"rating_2026_current":-16.4,"rank_2026_current":123,"rating_2025_eoy":-17.568411764705882,"rank_2025_eoy":126,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":1.1684117647058834,"rank_trend":3},"UAB":{"rating_2026_current":-18.1,"rank_2026_current":124,"rating_2025_eoy":-15.764411764705883,"rank_2025_eoy":123,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.335588235294118,"rank_trend":-1},"Northern Illinois":{"rating_2026_current":-18.2,"rank_2026_current":125,"rating_2025_eoy":-16.586411764705883,"rank_2025_eoy":124,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.6135882352941169,"rank_trend":-1},"Missouri State":{"rating_2026_current":-18.7,"rank_2026_current":126,"rating_2025_eoy":-12.21041176470588,"rank_2025_eoy":111,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-6.48958823529412,"rank_trend":-15},"Akron":{"rating_2026_current":-19.5,"rank_2026_current":127,"rating_2025_eoy":-17.656411764705883,"rank_2025_eoy":127,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-1.843588235294117,"rank_trend":0},"Kent State":{"rating_2026_current":-20.1,"rank_2026_current":128,"rating_2025_eoy":-20.28641176470588,"rank_2025_eoy":132,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":0.1864117647058769,"rank_trend":4},"UTEP":{"rating_2026_current":-20.5,"rank_2026_current":129,"rating_2025_eoy":-17.916411764705884,"rank_2025_eoy":128,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-2.5835882352941155,"rank_trend":-1},"Sacramento State":{"rating_2026_current":-22.7,"rank_2026_current":130,"rating_2025_eoy":null,"rank_2025_eoy":null,"source_count_2025":0,"missing_sources_2025":"spplus_2025,fpi_2025,teamrankings_2025,kford_2025,bradpowers_2025","rating_trend":null,"rank_trend":null},"Southern Miss":{"rating_2026_current":-23.3,"rank_2026_current":131,"rating_2025_eoy":-8.752411764705883,"rank_2025_eoy":98,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-14.547588235294118,"rank_trend":-33},"UL-Monroe":{"rating_2026_current":-24.3,"rank_2026_current":132,"rating_2025_eoy":-20.034411764705883,"rank_2025_eoy":131,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-4.265588235294118,"rank_trend":-1},"Georgia State":{"rating_2026_current":-25.1,"rank_2026_current":133,"rating_2025_eoy":-19.97641176470588,"rank_2025_eoy":130,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-5.123588235294122,"rank_trend":-3},"Ball State":{"rating_2026_current":-25.2,"rank_2026_current":134,"rating_2025_eoy":-21.98841176470588,"rank_2025_eoy":133,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-3.211588235294119,"rank_trend":-1},"Middle Tennessee":{"rating_2026_current":-26.0,"rank_2026_current":135,"rating_2025_eoy":-18.20441176470588,"rank_2025_eoy":129,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-7.795588235294119,"rank_trend":-6},"Sam Houston":{"rating_2026_current":-26.3,"rank_2026_current":136,"rating_2025_eoy":-25.76041176470589,"rank_2025_eoy":135,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-0.5395882352941115,"rank_trend":-1},"Massachusetts":{"rating_2026_current":-30.9,"rank_2026_current":137,"rating_2025_eoy":-33.532411764705884,"rank_2025_eoy":136,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":2.6324117647058856,"rank_trend":-1},"Charlotte":{"rating_2026_current":-32.4,"rank_2026_current":138,"rating_2025_eoy":-23.27641176470588,"rank_2025_eoy":134,"source_count_2025":5,"missing_sources_2025":null,"rating_trend":-9.123588235294118,"rank_trend":-4}};

const confBySlug = Object.fromEntries(DB.conferences.map(c => [c.slug, c]));
const weeks = [...new Set(DB.games.map(g => g.week))].sort((a,b)=>a-b);
const STAFF_2026 = {"Army":{"record_2025":"7-6","conf_record_2025":"4-5","head_coach":"Jeff Monken","head_coach_status":"returning","offensive_coordinator":"Cody Worley","oc_status":"returning","defensive_coordinator":"Daryl Dixon / Scot Sloan","dc_status":"new","head_coach_first_season":"2014"},"Charlotte":{"record_2025":"1-11","conf_record_2025":"0-8","head_coach":"Tim Albin","head_coach_status":"returning","offensive_coordinator":"Todd Fitch","oc_status":"returning","defensive_coordinator":"Nate Faanes","dc_status":"partial","head_coach_first_season":"2025"},"East Carolina":{"record_2025":"9-4","conf_record_2025":"6-2","head_coach":"Blake Harrell","head_coach_status":"returning","offensive_coordinator":"Jordan Davis","oc_status":"new","defensive_coordinator":"Jordan Hankins","dc_status":"new","head_coach_first_season":"2024"},"FAU":{"record_2025":"4-8","conf_record_2025":"3-5","head_coach":"Zach Kittley","head_coach_status":"returning","offensive_coordinator":"Zach Kittley","oc_status":"new","defensive_coordinator":"Brett Dewhurst","dc_status":"returning","head_coach_first_season":"2025"},"Memphis":{"record_2025":"8-5","conf_record_2025":"4-4","head_coach":"Charles Huff","head_coach_status":"new","offensive_coordinator":"Kevin Decker / David Weeks","oc_status":"new","defensive_coordinator":"Lance Guidry","dc_status":"new","head_coach_first_season":"2026"},"Navy":{"record_2025":"11-2","conf_record_2025":"8-1","head_coach":"Brian Newberry","head_coach_status":"returning","offensive_coordinator":"Drew Cronic","oc_status":"returning","defensive_coordinator":"Ricky Brown / Eric Lewis","dc_status":"new","head_coach_first_season":"2023"},"North Texas":{"record_2025":"12-2","conf_record_2025":"7-1","head_coach":"Neal Brown","head_coach_status":"new","offensive_coordinator":"Mike Bloesch","oc_status":"new","defensive_coordinator":"Bradley Dale Peveto / Matt Powledge","dc_status":"new","head_coach_first_season":"2026"},"Rice":{"record_2025":"5-8","conf_record_2025":"2-6","head_coach":"Scott Abell","head_coach_status":"returning","offensive_coordinator":"Vince Munch","oc_status":"returning","defensive_coordinator":"Jon Kay","dc_status":"returning","head_coach_first_season":"2025"},"USF":{"record_2025":"9-4","conf_record_2025":"6-2","head_coach":"Brian Hartline","head_coach_status":"new","offensive_coordinator":"Tim Beck","oc_status":"new","defensive_coordinator":"Josh Aldridge","dc_status":"new","head_coach_first_season":"2026"},"Temple":{"record_2025":"5-7","conf_record_2025":"3-5","head_coach":"K. C. Keeler","head_coach_status":"returning","offensive_coordinator":"Tyler Walker","oc_status":"returning","defensive_coordinator":"Brian Smith","dc_status":"returning","head_coach_first_season":"2025"},"Tulane":{"record_2025":"11-3","conf_record_2025":"7-1","head_coach":"Will Hall","head_coach_status":"new","offensive_coordinator":"Russ Callaway","oc_status":"new","defensive_coordinator":"Nate Fuqua / Tayler Polk","dc_status":"partial","head_coach_first_season":"2026"},"Tulsa":{"record_2025":"4-8","conf_record_2025":"1-7","head_coach":"Tre Lamb","head_coach_status":"returning","offensive_coordinator":"Kevin Barbay / Ty Darlington","oc_status":"partial","defensive_coordinator":"Mike Gray / Josh Reardon","dc_status":"returning","head_coach_first_season":"2025"},"UAB":{"record_2025":"4-8","conf_record_2025":"2-6","head_coach":"Alex Mortensen","head_coach_status":"returning","offensive_coordinator":"Alex Mortensen","oc_status":"returning","defensive_coordinator":"Todd Grantham","dc_status":"new","head_coach_first_season":"2025"},"UTSA":{"record_2025":"7-6","conf_record_2025":"4-4","head_coach":"Jeff Traylor","head_coach_status":"returning","offensive_coordinator":"Rick Bowie","oc_status":"new","defensive_coordinator":"Jess Loepp","dc_status":"returning","head_coach_first_season":"2020"},"Boston College":{"record_2025":"2-10","conf_record_2025":"1-7","head_coach":"Bill O'Brien","head_coach_status":"returning","offensive_coordinator":"Bill O'Brien","oc_status":"new","defensive_coordinator":"Ted Roof","dc_status":"new","head_coach_first_season":"2024"},"California":{"record_2025":"7-6","conf_record_2025":"4-4","head_coach":"Tosh Lupoi","head_coach_status":"new","offensive_coordinator":"Jordan Somerville","oc_status":"new","defensive_coordinator":"Da'Von Brown / Michael Hutchings","dc_status":"new","head_coach_first_season":"2026"},"Clemson":{"record_2025":"7-6","conf_record_2025":"4-4","head_coach":"Dabo Swinney","head_coach_status":"returning","offensive_coordinator":"Chad Morris","oc_status":"new","defensive_coordinator":"Tom Allen","dc_status":"partial","head_coach_first_season":"2009"},"Duke":{"record_2025":"9-5","conf_record_2025":"6-2","head_coach":"Manny Diaz","head_coach_status":"returning","offensive_coordinator":"Jonathan Brewer","oc_status":"returning","defensive_coordinator":"Jonathan Patke","dc_status":"returning","head_coach_first_season":"2024"},"Florida State":{"record_2025":"5-7","conf_record_2025":"2-6","head_coach":"Mike Norvell","head_coach_status":"returning","offensive_coordinator":"Tim Harris Jr.","oc_status":"new","defensive_coordinator":"Tony White","dc_status":"returning","head_coach_first_season":"2020"},"Georgia Tech":{"record_2025":"9-4","conf_record_2025":"6-2","head_coach":"Brent Key","head_coach_status":"returning","offensive_coordinator":"George Godsey / Chris Weinke","oc_status":"new","defensive_coordinator":"Jason Semore","dc_status":"new","head_coach_first_season":"2022"},"Louisville":{"record_2025":"9-4","conf_record_2025":"4-4","head_coach":"Jeff Brohm","head_coach_status":"returning","offensive_coordinator":"Brian Brohm","oc_status":"returning","defensive_coordinator":"Steve Ellis / Mark Ivey","dc_status":"new","head_coach_first_season":"2023"},"Miami-FL":{"record_2025":"13-3","conf_record_2025":"6-2","head_coach":"Mario Cristobal","head_coach_status":"returning","offensive_coordinator":"Shannon Dawson","oc_status":"returning","defensive_coordinator":"Corey Hetherman","dc_status":"returning","head_coach_first_season":"2022"},"North Carolina":{"record_2025":"4-8","conf_record_2025":"2-6","head_coach":"Bill Belichick","head_coach_status":"returning","offensive_coordinator":"Bobby Petrino","oc_status":"new","defensive_coordinator":"Stephen Belichick","dc_status":"returning","head_coach_first_season":"2025"},"NC State":{"record_2025":"8-5","conf_record_2025":"4-4","head_coach":"Dave Doeren","head_coach_status":"returning","offensive_coordinator":"Kurt Roper","oc_status":"returning","defensive_coordinator":"D. J. Eliot / Charlton Warren","dc_status":"returning","head_coach_first_season":"2013"},"Pittsburgh":{"record_2025":"8-5","conf_record_2025":"6-2","head_coach":"Pat Narduzzi","head_coach_status":"returning","offensive_coordinator":"Kade Bell","oc_status":"returning","defensive_coordinator":"Cory Sanders","dc_status":"new","head_coach_first_season":"2015"},"SMU":{"record_2025":"9-4","conf_record_2025":"6-2","head_coach":"Rhett Lashlee","head_coach_status":"returning","offensive_coordinator":"Garin Justice / D'Eriq King / Rob Likens","oc_status":"partial","defensive_coordinator":"Maurice Crum Jr. / Rickey Hunley Jr.","dc_status":"new","head_coach_first_season":"2022"},"Stanford":{"record_2025":"4-8","conf_record_2025":"3-5","head_coach":"Tavita Pritchard","head_coach_status":"new","offensive_coordinator":"Terry Heffernan","oc_status":"new","defensive_coordinator":"Kris Richard","dc_status":"new","head_coach_first_season":"2026"},"Syracuse":{"record_2025":"3-9","conf_record_2025":"1-7","head_coach":"Fran Brown","head_coach_status":"returning","offensive_coordinator":"Mike Johnson / Jeff Nixon","oc_status":"returning","defensive_coordinator":"Vince Kehres","dc_status":"new","head_coach_first_season":"2024"},"Virginia":{"record_2025":"11-3","conf_record_2025":"7-1","head_coach":"Tony Elliott","head_coach_status":"returning","offensive_coordinator":"Des Kitchings","oc_status":"returning","defensive_coordinator":"John Rudzinski","dc_status":"returning","head_coach_first_season":"2022"},"Virginia Tech":{"record_2025":"3-9","conf_record_2025":"2-6","head_coach":"James Franklin","head_coach_status":"new","offensive_coordinator":"Ty Howle","oc_status":"new","defensive_coordinator":"Brent Pry","dc_status":"new","head_coach_first_season":"2026"},"Wake Forest":{"record_2025":"9-4","conf_record_2025":"4-4","head_coach":"Jake Dickert","head_coach_status":"returning","offensive_coordinator":"Rob Ezell","oc_status":"returning","defensive_coordinator":"Scottie Hazelton","dc_status":"returning","head_coach_first_season":"2025"},"Arizona":{"record_2025":"9-4","conf_record_2025":"6-3","head_coach":"Brent Brennan","head_coach_status":"returning","offensive_coordinator":"Seth Doege","oc_status":"returning","defensive_coordinator":"Danny Gonzales","dc_status":"returning","head_coach_first_season":"2024"},"Arizona State":{"record_2025":"8-5","conf_record_2025":"6-3","head_coach":"Kenny Dillingham","head_coach_status":"returning","offensive_coordinator":"Marcus Arroyo","oc_status":"returning","defensive_coordinator":"Brian Ward","dc_status":"returning","head_coach_first_season":"2023"},"Baylor":{"record_2025":"5-7","conf_record_2025":"3-6","head_coach":"Dave Aranda","head_coach_status":"returning","offensive_coordinator":"Jake Spavital","oc_status":"returning","defensive_coordinator":"Joe Klanderman","dc_status":"new","head_coach_first_season":"2020"},"BYU":{"record_2025":"12-2","conf_record_2025":"8-1","head_coach":"Kalani Sitake","head_coach_status":"returning","offensive_coordinator":"Aaron Roderick","oc_status":"returning","defensive_coordinator":"Kelly Poppinga","dc_status":"new","head_coach_first_season":"2016"},"Cincinnati":{"record_2025":"7-6","conf_record_2025":"5-4","head_coach":"Scott Satterfield","head_coach_status":"returning","offensive_coordinator":"Nic Cardwell / Pete Thomas","oc_status":"new","defensive_coordinator":"Nate Woody","dc_status":"new","head_coach_first_season":"2023"},"Colorado":{"record_2025":"3-9","conf_record_2025":"1-8","head_coach":"Deion Sanders","head_coach_status":"returning","offensive_coordinator":"Brennan Marion","oc_status":"new","defensive_coordinator":"Chris Marve","dc_status":"new","head_coach_first_season":"2023"},"Houston":{"record_2025":"10-3","conf_record_2025":"6-3","head_coach":"Willie Fritz","head_coach_status":"returning","offensive_coordinator":"Slade Nagle","oc_status":"returning","defensive_coordinator":"Austin Armstrong","dc_status":"returning","head_coach_first_season":"2024"},"Iowa State":{"record_2025":"8-4","conf_record_2025":"5-4","head_coach":"Jimmy Rogers","head_coach_status":"new","offensive_coordinator":"Tyler Roehl","oc_status":"new","defensive_coordinator":"Jesse Bobbit","dc_status":"new","head_coach_first_season":"2026"},"Kansas":{"record_2025":"5-7","conf_record_2025":"3-6","head_coach":"Lance Leipold","head_coach_status":"returning","offensive_coordinator":"Andy Kotelnicki / Matt Lubick","oc_status":"partial","defensive_coordinator":"D.K. McDonald","dc_status":"returning","head_coach_first_season":"2021"},"Kansas State":{"record_2025":"6-6","conf_record_2025":"5-4","head_coach":"Collin Klein","head_coach_status":"new","offensive_coordinator":"Sean Gleeson","oc_status":"new","defensive_coordinator":"Jordan Peterson","dc_status":"new","head_coach_first_season":"2026"},"Oklahoma State":{"record_2025":"1-11","conf_record_2025":"0-9","head_coach":"Eric Morris","head_coach_status":"new","offensive_coordinator":"Sean Brophy","oc_status":"new","defensive_coordinator":"Skyler Cassity","dc_status":"new","head_coach_first_season":"2026"},"TCU":{"record_2025":"9-4","conf_record_2025":"5-4","head_coach":"Sonny Dykes","head_coach_status":"returning","offensive_coordinator":"A. J. Ricker / Gordon Sammis","oc_status":"partial","defensive_coordinator":"Andy Avalos","dc_status":"returning","head_coach_first_season":"2022"},"Texas Tech":{"record_2025":"12-2","conf_record_2025":"8-1","head_coach":"Joey McGuire","head_coach_status":"returning","offensive_coordinator":"Mack Leftwich","oc_status":"returning","defensive_coordinator":"Rob Greene / Shiel Wood","dc_status":"partial","head_coach_first_season":"2022"},"UCF":{"record_2025":"5-7","conf_record_2025":"2-7","head_coach":"Scott Frost","head_coach_status":"returning","offensive_coordinator":"Steve Cooper","oc_status":"returning","defensive_coordinator":"Alex Grinch","dc_status":"returning","head_coach_first_season":"2025"},"Utah":{"record_2025":"11-2","conf_record_2025":"7-2","head_coach":"Morgan Scalley","head_coach_status":"new","offensive_coordinator":"Kevin McGiven","oc_status":"new","defensive_coordinator":"Colton Swan","dc_status":"new","head_coach_first_season":"2026"},"West Virginia":{"record_2025":"4-8","conf_record_2025":"2-7","head_coach":"Rich Rodriguez","head_coach_status":"returning","offensive_coordinator":"Rich Rodriguez","oc_status":"returning","defensive_coordinator":"Zac Alley","dc_status":"returning","head_coach_first_season":"2025"},"Illinois":{"record_2025":"9-4","conf_record_2025":"5-4","head_coach":"Bret Bielema","head_coach_status":"returning","offensive_coordinator":"Barry Lunney Jr.","oc_status":"returning","defensive_coordinator":"Bobby Hauck","dc_status":"new","head_coach_first_season":"2021"},"Indiana":{"record_2025":"16-0","conf_record_2025":"9-0","head_coach":"Curt Cignetti","head_coach_status":"returning","offensive_coordinator":"Mike Shanahan","oc_status":"partial","defensive_coordinator":"Bryant Haines","dc_status":"returning","head_coach_first_season":"2024"},"Iowa":{"record_2025":"9-4","conf_record_2025":"6-3","head_coach":"Kirk Ferentz","head_coach_status":"returning","offensive_coordinator":"Tim Lester","oc_status":"returning","defensive_coordinator":"Phil Parker","dc_status":"returning","head_coach_first_season":"1999"},"Maryland":{"record_2025":"4-8","conf_record_2025":"1-8","head_coach":"Mike Locksley","head_coach_status":"returning","offensive_coordinator":"Clint Trickett","oc_status":"new","defensive_coordinator":"Aazaar Abdul-Rahim / Ted Monachino","dc_status":"returning","head_coach_first_season":"2019"},"Michigan":{"record_2025":"9-4","conf_record_2025":"7-2","head_coach":"Kyle Whittingham","head_coach_status":"new","offensive_coordinator":"Jason Beck","oc_status":"new","defensive_coordinator":"Jay Hill","dc_status":"new","head_coach_first_season":"2026"},"Michigan State":{"record_2025":"4-8","conf_record_2025":"1-8","head_coach":"Pat Fitzgerald","head_coach_status":"new","offensive_coordinator":"Nick Sheridan","oc_status":"new","defensive_coordinator":"Max Bullough / Joe Rossi","dc_status":"partial","head_coach_first_season":"2026"},"Minnesota":{"record_2025":"8-5","conf_record_2025":"5-4","head_coach":"P. J. Fleck","head_coach_status":"returning","offensive_coordinator":"Greg Harbaugh Jr. / Matt Simon","oc_status":"returning","defensive_coordinator":"Danny Collins","dc_status":"returning","head_coach_first_season":"2017"},"Nebraska":{"record_2025":"7-6","conf_record_2025":"4-5","head_coach":"Matt Rhule","head_coach_status":"returning","offensive_coordinator":"Dana Holgorsen","oc_status":"returning","defensive_coordinator":"Rob Aurich","dc_status":"new","head_coach_first_season":"2023"},"Northwestern":{"record_2025":"7-6","conf_record_2025":"4-5","head_coach":"David Braun","head_coach_status":"returning","offensive_coordinator":"Chip Kelly","oc_status":"new","defensive_coordinator":"Tim McGarigle","dc_status":"returning","head_coach_first_season":"2023"},"Ohio State":{"record_2025":"12-2","conf_record_2025":"9-0","head_coach":"Ryan Day","head_coach_status":"returning","offensive_coordinator":"Keenan Bailey / Arthur Smith","oc_status":"partial","defensive_coordinator":"Matt Patricia / Tim Walton","dc_status":"returning","head_coach_first_season":"2019"},"Oregon":{"record_2025":"13-2","conf_record_2025":"8-1","head_coach":"Dan Lanning","head_coach_status":"returning","offensive_coordinator":"Drew Mehringer","oc_status":"new","defensive_coordinator":"Chris Hampton","dc_status":"partial","head_coach_first_season":"2022"},"Penn State":{"record_2025":"7-6","conf_record_2025":"3-6","head_coach":"Matt Campbell","head_coach_status":"new","offensive_coordinator":"Taylor Mouser","oc_status":"new","defensive_coordinator":"D'Anton Lynn","dc_status":"new","head_coach_first_season":"2026"},"Purdue":{"record_2025":"2-10","conf_record_2025":"0-9","head_coach":"Barry Odom","head_coach_status":"returning","offensive_coordinator":"Josh Henson","oc_status":"returning","defensive_coordinator":"Kevin Kane","dc_status":"new","head_coach_first_season":"2025"},"Rutgers":{"record_2025":"5-7","conf_record_2025":"2-7","head_coach":"Greg Schiano","head_coach_status":"returning","offensive_coordinator":"Kirk Ciarrocca","oc_status":"returning","defensive_coordinator":"Travis Johansen","dc_status":"new","head_coach_first_season":"2020"},"UCLA":{"record_2025":"3-9","conf_record_2025":"3-6","head_coach":"Bob Chesney","head_coach_status":"new","offensive_coordinator":"Dean Kennedy","oc_status":"new","defensive_coordinator":"Colin Hitschler","dc_status":"new","head_coach_first_season":"2026"},"USC":{"record_2025":"9-4","conf_record_2025":"7-2","head_coach":"Lincoln Riley","head_coach_status":"returning","offensive_coordinator":"Luke Huard","oc_status":"returning","defensive_coordinator":"Gary Patterson","dc_status":"new","head_coach_first_season":"2022"},"Washington":{"record_2025":"9-4","conf_record_2025":"5-4","head_coach":"Jedd Fisch","head_coach_status":"returning","offensive_coordinator":"Jedd Fisch","oc_status":"new","defensive_coordinator":"Ryan Walters","dc_status":"returning","head_coach_first_season":"2024"},"Wisconsin":{"record_2025":"4-8","conf_record_2025":"2-7","head_coach":"Luke Fickell","head_coach_status":"returning","offensive_coordinator":"Jeff Grimes","oc_status":"returning","defensive_coordinator":"Mike Tressel","dc_status":"returning","head_coach_first_season":"2023"},"Delaware":{"record_2025":"7-6","conf_record_2025":"4-4","head_coach":"Ryan Carty","head_coach_status":"returning","offensive_coordinator":"Terence Archer","oc_status":"returning","defensive_coordinator":"Manny Rojas","dc_status":"returning","head_coach_first_season":"2022"},"FIU":{"record_2025":"7-6","conf_record_2025":"5-3","head_coach":"Willie Simmons","head_coach_status":"returning","offensive_coordinator":"Nick Coleman","oc_status":"returning","defensive_coordinator":"Jovan Dewitt","dc_status":"returning","head_coach_first_season":"2025"},"Jacksonville State":{"record_2025":"9-5","conf_record_2025":"7-1","head_coach":"Charles Kelly","head_coach_status":"returning","offensive_coordinator":"Taylor Housewright","oc_status":"new","defensive_coordinator":"Brian Williams","dc_status":"returning","head_coach_first_season":"2025"},"Kennesaw State":{"record_2025":"10-4","conf_record_2025":"7-1","head_coach":"Jerry Mack","head_coach_status":"returning","offensive_coordinator":"Mitch Militello","oc_status":"returning","defensive_coordinator":"Marc Mattioli","dc_status":"returning","head_coach_first_season":"2025"},"Liberty":{"record_2025":"4-8","conf_record_2025":"3-5","head_coach":"Jamey Chadwell","head_coach_status":"returning","offensive_coordinator":"Newland Isaac","oc_status":"partial","defensive_coordinator":"Skylor Magee","dc_status":"partial","head_coach_first_season":"2023"},"Louisiana Tech":{"record_2025":"8-5","conf_record_2025":"5-3","head_coach":"Sonny Cumbie","head_coach_status":"returning","offensive_coordinator":"Nathan Young","oc_status":"new","defensive_coordinator":"Luke Olson","dc_status":"returning","head_coach_first_season":"2022"},"Middle Tennessee":{"record_2025":"3-9","conf_record_2025":"2-6","head_coach":"Derek Mason","head_coach_status":"returning","offensive_coordinator":"Anthony Scelfo","oc_status":"new","defensive_coordinator":"Brian Stewart","dc_status":"returning","head_coach_first_season":"2024"},"Missouri State":{"record_2025":"7-6","conf_record_2025":"5-3","head_coach":"Casey Woods","head_coach_status":"new","offensive_coordinator":"Mark Cala","oc_status":"new","defensive_coordinator":"Jack Curtis","dc_status":"new","head_coach_first_season":"2026"},"New Mexico State":{"record_2025":"4-8","conf_record_2025":"2-6","head_coach":"Tony Sanchez","head_coach_status":"returning","offensive_coordinator":"David Yost","oc_status":"returning","defensive_coordinator":"Joe Morris","dc_status":"returning","head_coach_first_season":"2024"},"Sam Houston":{"record_2025":"2-10","conf_record_2025":"1-7","head_coach":"Phil Longo","head_coach_status":"returning","offensive_coordinator":"Zack Patterson","oc_status":"returning","defensive_coordinator":"Freddie Aughtry-Lindsay","dc_status":"returning","head_coach_first_season":"2025"},"Western Kentucky":{"record_2025":"9-4","conf_record_2025":"6-2","head_coach":"Tyson Helton","head_coach_status":"returning","offensive_coordinator":"Joe Bernardi / Bodie Reeder","oc_status":"new","defensive_coordinator":"Davis Merritt","dc_status":"partial","head_coach_first_season":"2019"},"Notre Dame":{"record_2025":"10-2","conf_record_2025":"0-0","head_coach":"Marcus Freeman","head_coach_status":"returning","offensive_coordinator":"Mike Denbrock","oc_status":"returning","defensive_coordinator":"Chris Ash / Aaron Henry","dc_status":"partial","head_coach_first_season":"2022"},"Connecticut":{"record_2025":"9-4","conf_record_2025":"0-0","head_coach":"Jason Candle","head_coach_status":"new","offensive_coordinator":"Marquel Blackwell / Nunzio Campanile","oc_status":"unverified","defensive_coordinator":"Ryan Manalac","dc_status":"unverified","head_coach_first_season":"2026"},"Akron":{"record_2025":"5-7","conf_record_2025":"4-4","head_coach":"Joe Moorhead","head_coach_status":"returning","offensive_coordinator":"Joe Moorhead","oc_status":"returning","defensive_coordinator":"Tim Tibesar","dc_status":"returning","head_coach_first_season":"2022"},"Ball State":{"record_2025":"4-8","conf_record_2025":"3-5","head_coach":"Mike Uremovich","head_coach_status":"returning","offensive_coordinator":"Mike Uremovich","oc_status":"returning","defensive_coordinator":"Jeff Knowles","dc_status":"returning","head_coach_first_season":"2025"},"Bowling Green":{"record_2025":"4-8","conf_record_2025":"2-6","head_coach":"Eddie George","head_coach_status":"returning","offensive_coordinator":"Greg Nosal","oc_status":"new","defensive_coordinator":"Joe Bowden","dc_status":"new","head_coach_first_season":"2025"},"Buffalo":{"record_2025":"5-7","conf_record_2025":"4-4","head_coach":"Pete Lembo","head_coach_status":"returning","offensive_coordinator":"Tony Tokarz","oc_status":"new","defensive_coordinator":"Brian Dougherty","dc_status":"new","head_coach_first_season":"2024"},"Central Michigan":{"record_2025":"7-6","conf_record_2025":"5-3","head_coach":"Matt Drinkall","head_coach_status":"returning","offensive_coordinator":"Jim Chapin / Derek Fulton","oc_status":"returning","defensive_coordinator":"Sean Cronin","dc_status":"returning","head_coach_first_season":"2025"},"Eastern Michigan":{"record_2025":"4-8","conf_record_2025":"3-5","head_coach":"Chris Creighton","head_coach_status":"returning","offensive_coordinator":"Mike Piatkowski","oc_status":"returning","defensive_coordinator":"Tate Omli / Kasey Teegardin","dc_status":"new","head_coach_first_season":"2014"},"Kent State":{"record_2025":"5-7","conf_record_2025":"4-4","head_coach":"Mark Carney","head_coach_status":"returning","offensive_coordinator":"Clay Patterson","oc_status":"returning","defensive_coordinator":"Cherokee Valeria","dc_status":"returning","head_coach_first_season":"2025"},"Miami-OH":{"record_2025":"7-7","conf_record_2025":"6-2","head_coach":"Chuck Martin","head_coach_status":"returning","offensive_coordinator":"Gus Ragland","oc_status":"new","defensive_coordinator":"Bill Brechin","dc_status":"returning","head_coach_first_season":"2014"},"Ohio":{"record_2025":"9-4","conf_record_2025":"6-2","head_coach":"John Hauser","head_coach_status":"returning","offensive_coordinator":"Scott Isophording","oc_status":"new","defensive_coordinator":"Kurt Mattix","dc_status":"new","head_coach_first_season":"2025"},"Sacramento State":{"record_2025":"7-5","conf_record_2025":"5-3","head_coach":"Alonzo Carter","head_coach_status":"new","offensive_coordinator":"Eric Kiesau / Eric Scott","oc_status":"unverified","defensive_coordinator":"Adam Clark / Kenwick Thompson","dc_status":"unverified","head_coach_first_season":"2026"},"Toledo":{"record_2025":"8-5","conf_record_2025":"6-2","head_coach":"Mike Jacobs","head_coach_status":"new","offensive_coordinator":"Cris Reisert","oc_status":"new","defensive_coordinator":"Jahmal Brown","dc_status":"new","head_coach_first_season":"2026"},"UMass":{"record_2025":"0-12","conf_record_2025":"0-8","head_coach":"Joe Harasymiak","head_coach_status":"returning","offensive_coordinator":"Max Warner","oc_status":"new","defensive_coordinator":"Jared Keyte","dc_status":"returning","head_coach_first_season":"2025"},"Western Michigan":{"record_2025":"10-4","conf_record_2025":"7-1","head_coach":"Lance Taylor","head_coach_status":"returning","offensive_coordinator":"Walt Bell","oc_status":"returning","defensive_coordinator":"Greer Martini / Duane Vaughn","dc_status":"new","head_coach_first_season":"2023"},"Air Force":{"record_2025":"4-8","conf_record_2025":"3-5","head_coach":"Troy Calhoun","head_coach_status":"returning","offensive_coordinator":"Mike Thiessen","oc_status":"returning","defensive_coordinator":"Steve Russ","dc_status":"new","head_coach_first_season":"2007"},"Hawaii":{"record_2025":"9-4","conf_record_2025":"5-3","head_coach":"Timmy Chang","head_coach_status":"returning","offensive_coordinator":"Anthony Arceneaux","oc_status":"returning","defensive_coordinator":"Dennis Thurman","dc_status":"returning","head_coach_first_season":"2022"},"Nevada":{"record_2025":"3-9","conf_record_2025":"2-6","head_coach":"Jeff Choate","head_coach_status":"returning","offensive_coordinator":"Bret Bartalone","oc_status":"new","defensive_coordinator":"Kane Ioane","dc_status":"returning","head_coach_first_season":"2024"},"New Mexico":{"record_2025":"9-4","conf_record_2025":"6-2","head_coach":"Jason Eck","head_coach_status":"returning","offensive_coordinator":"Luke Schleusner","oc_status":"returning","defensive_coordinator":"Spence Nowinsky","dc_status":"returning","head_coach_first_season":"2025"},"North Dakota State":{"record_2025":"12-1","conf_record_2025":"8-0","head_coach":"Tim Polasek","head_coach_status":"returning","offensive_coordinator":"Dan Larson","oc_status":"unverified","defensive_coordinator":"Grant Olson","dc_status":"unverified","head_coach_first_season":"2024"},"Northern Illinois":{"record_2025":"3-9","conf_record_2025":"2-6","head_coach":"Rob Harley (interim)","head_coach_status":"new","offensive_coordinator":"Tony Petersen","oc_status":"new","defensive_coordinator":"D. J. Bland","dc_status":"new","head_coach_first_season":"2026"},"San Jose State":{"record_2025":"3-9","conf_record_2025":"2-6","head_coach":"Ken Niumatalolo","head_coach_status":"returning","offensive_coordinator":"Craig Stutzmann","oc_status":"returning","defensive_coordinator":"Bojay Filimoeatu","dc_status":"new","head_coach_first_season":"2024"},"UNLV":{"record_2025":"10-4","conf_record_2025":"6-2","head_coach":"Dan Mullen","head_coach_status":"returning","offensive_coordinator":"Corey Dennis","oc_status":"returning","defensive_coordinator":"Paul Guenther","dc_status":"returning","head_coach_first_season":"2025"},"UTEP":{"record_2025":"2-10","conf_record_2025":"1-7","head_coach":"Scotty Walden","head_coach_status":"returning","offensive_coordinator":"Joe Pappalardo / Lanear Sampson","oc_status":"new","defensive_coordinator":"Kyle Beyer / Kelvin Sigler","dc_status":"partial","head_coach_first_season":"2024"},"Wyoming":{"record_2025":"4-8","conf_record_2025":"2-6","head_coach":"Jay Sawvel","head_coach_status":"returning","offensive_coordinator":"Christian Taylor","oc_status":"new","defensive_coordinator":"Aaron Bohl","dc_status":"returning","head_coach_first_season":"2024"},"Boise State":{"record_2025":"9-5","conf_record_2025":"6-2","head_coach":"Spencer Danielson","head_coach_status":"returning","offensive_coordinator":"Nate Potter","oc_status":"partial","defensive_coordinator":"Erik Chinander","dc_status":"partial","head_coach_first_season":"2023"},"Colorado State":{"record_2025":"2-10","conf_record_2025":"1-7","head_coach":"Jim Mora","head_coach_status":"new","offensive_coordinator":"Pryce Tracy","oc_status":"new","defensive_coordinator":"Tyson Summers","dc_status":"returning","head_coach_first_season":"2026"},"Fresno State":{"record_2025":"9-4","conf_record_2025":"5-3","head_coach":"Matt Entz","head_coach_status":"returning","offensive_coordinator":"Josh Davis","oc_status":"returning","defensive_coordinator":"Nick Benedetto","dc_status":"returning","head_coach_first_season":"2025"},"Oregon State":{"record_2025":"2-10","conf_record_2025":"1-1","head_coach":"JaMarcus Shephard","head_coach_status":"new","offensive_coordinator":"Mitch Dahlen","oc_status":"new","defensive_coordinator":"Mike MacIntyre","dc_status":"new","head_coach_first_season":"2026"},"San Diego State":{"record_2025":"9-4","conf_record_2025":"6-2","head_coach":"Sean Lewis","head_coach_status":"returning","offensive_coordinator":"Sean Lewis","oc_status":"returning","defensive_coordinator":"Demetrius Sumler","dc_status":"new","head_coach_first_season":"2024"},"Texas State":{"record_2025":"7-6","conf_record_2025":"3-5","head_coach":"G. J. Kinne","head_coach_status":"returning","offensive_coordinator":"Landon Keopple","oc_status":"returning","defensive_coordinator":"Will Windham","dc_status":"new","head_coach_first_season":"2023"},"Utah State":{"record_2025":"6-7","conf_record_2025":"4-4","head_coach":"Bronco Mendenhall","head_coach_status":"returning","offensive_coordinator":"Robert Anae","oc_status":"new","defensive_coordinator":"Nick Howell","dc_status":"returning","head_coach_first_season":"2025"},"Washington State":{"record_2025":"7-6","conf_record_2025":"1-1","head_coach":"Kirby Moore","head_coach_status":"new","offensive_coordinator":"Matt Miller","oc_status":"new","defensive_coordinator":"Trent Bray","dc_status":"new","head_coach_first_season":"2026"},"Alabama":{"record_2025":"11-4","conf_record_2025":"7-1","head_coach":"Kalen DeBoer","head_coach_status":"returning","offensive_coordinator":"Ryan Grubb","oc_status":"partial","defensive_coordinator":"Maurice Linguist / Kane Wommack","dc_status":"returning","head_coach_first_season":"2024"},"Arkansas":{"record_2025":"2-10","conf_record_2025":"0-8","head_coach":"Ryan Silverfield","head_coach_status":"new","offensive_coordinator":"Tim Cramsey","oc_status":"new","defensive_coordinator":"Ron Roberts","dc_status":"new","head_coach_first_season":"2026"},"Auburn":{"record_2025":"5-7","conf_record_2025":"1-7","head_coach":"Alex Golesh","head_coach_status":"new","offensive_coordinator":"Kodi Burns / Joel Gordon","oc_status":"new","defensive_coordinator":"D.J. Durkin","dc_status":"new","head_coach_first_season":"2026"},"Florida":{"record_2025":"4-8","conf_record_2025":"2-6","head_coach":"Jon Sumrall","head_coach_status":"new","offensive_coordinator":"Buster Faulkner","oc_status":"new","defensive_coordinator":"Brad White","dc_status":"new","head_coach_first_season":"2026"},"Georgia":{"record_2025":"12-2","conf_record_2025":"7-1","head_coach":"Kirby Smart","head_coach_status":"returning","offensive_coordinator":"Mike Bobo","oc_status":"returning","defensive_coordinator":"Travaris Robinson / Glenn Schumann","dc_status":"returning","head_coach_first_season":"2016"},"Kentucky":{"record_2025":"5-7","conf_record_2025":"2-6","head_coach":"Will Stein","head_coach_status":"new","offensive_coordinator":"Joe Sloan","oc_status":"new","defensive_coordinator":"Jay Bateman","dc_status":"new","head_coach_first_season":"2026"},"LSU":{"record_2025":"7-6","conf_record_2025":"3-5","head_coach":"Lane Kiffin","head_coach_status":"new","offensive_coordinator":"Charlie Weis Jr.","oc_status":"new","defensive_coordinator":"Blake Baker","dc_status":"returning","head_coach_first_season":"2026"},"Mississippi State":{"record_2025":"5-8","conf_record_2025":"1-7","head_coach":"Jeff Lebby","head_coach_status":"returning","offensive_coordinator":"Jeff Lebby","oc_status":"returning","defensive_coordinator":"Zach Arnett / Matt Brock","dc_status":"new","head_coach_first_season":"2024"},"Missouri":{"record_2025":"8-5","conf_record_2025":"4-4","head_coach":"Eli Drinkwitz","head_coach_status":"returning","offensive_coordinator":"Chip Lindsey","oc_status":"new","defensive_coordinator":"Corey Batoon / Derek Nicholson","dc_status":"partial","head_coach_first_season":"2020"},"Oklahoma":{"record_2025":"10-3","conf_record_2025":"6-2","head_coach":"Brent Venables","head_coach_status":"returning","offensive_coordinator":"Ben Arbuckle","oc_status":"returning","defensive_coordinator":"Todd Bates","dc_status":"partial","head_coach_first_season":"2022"},"Ole Miss":{"record_2025":"13-2","conf_record_2025":"7-1","head_coach":"Pete Golding","head_coach_status":"returning","offensive_coordinator":"John David Baker","oc_status":"new","defensive_coordinator":"Bryan Brown","dc_status":"partial","head_coach_first_season":"2025"},"South Carolina":{"record_2025":"4-8","conf_record_2025":"1-7","head_coach":"Shane Beamer","head_coach_status":"returning","offensive_coordinator":"Kendal Briles","oc_status":"new","defensive_coordinator":"Torrian Gray / Clayton White","dc_status":"partial","head_coach_first_season":"2021"},"Tennessee":{"record_2025":"8-5","conf_record_2025":"4-4","head_coach":"Josh Heupel","head_coach_status":"returning","offensive_coordinator":"Joey Halzle","oc_status":"returning","defensive_coordinator":"Jim Knowles","dc_status":"new","head_coach_first_season":"2021"},"Texas":{"record_2025":"10-3","conf_record_2025":"6-2","head_coach":"Steve Sarkisian","head_coach_status":"returning","offensive_coordinator":"Kyle Flood","oc_status":"returning","defensive_coordinator":"Will Muschamp / Johnny Nansen","dc_status":"partial","head_coach_first_season":"2021"},"Texas A&M":{"record_2025":"11-2","conf_record_2025":"7-1","head_coach":"Mike Elko","head_coach_status":"returning","offensive_coordinator":"Holmon Wiggins","oc_status":"unverified","defensive_coordinator":"Lyle Hemphill / Elijah Robinson","dc_status":"unverified","head_coach_first_season":"2024"},"Vanderbilt":{"record_2025":"10-3","conf_record_2025":"6-2","head_coach":"Clark Lea","head_coach_status":"returning","offensive_coordinator":"Tim Beck","oc_status":"returning","defensive_coordinator":"Steve Gregory","dc_status":"returning","head_coach_first_season":"2021"},"Appalachian State":{"record_2025":"5-8","conf_record_2025":"2-6","head_coach":"Dowell Loggains","head_coach_status":"returning","offensive_coordinator":"Mike Anthony","oc_status":"new","defensive_coordinator":"D. J. Smith","dc_status":"returning","head_coach_first_season":"2025"},"Arkansas State":{"record_2025":"7-6","conf_record_2025":"5-3","head_coach":"Butch Jones","head_coach_status":"returning","offensive_coordinator":"Garrett Altman","oc_status":"new","defensive_coordinator":"Griffin McCarley","dc_status":"returning","head_coach_first_season":"2021"},"Coastal Carolina":{"record_2025":"6-7","conf_record_2025":"5-3","head_coach":"Ryan Beard","head_coach_status":"new","offensive_coordinator":"Nick Petrino","oc_status":"new","defensive_coordinator":"LD Scott","dc_status":"new","head_coach_first_season":"2026"},"Georgia Southern":{"record_2025":"7-6","conf_record_2025":"4-4","head_coach":"Clay Helton","head_coach_status":"returning","offensive_coordinator":"Ryan Aplin","oc_status":"returning","defensive_coordinator":"Mike Mutz","dc_status":"new","head_coach_first_season":"2022"},"Georgia State":{"record_2025":"1-11","conf_record_2025":"0-8","head_coach":"Dell McGee","head_coach_status":"returning","offensive_coordinator":"Hue Jackson","oc_status":"returning","defensive_coordinator":"Cam Clark / John Haneline","dc_status":"new","head_coach_first_season":"2024"},"James Madison":{"record_2025":"12-2","conf_record_2025":"8-0","head_coach":"Billy Napier","head_coach_status":"new","offensive_coordinator":"Cam Aiken","oc_status":"new","defensive_coordinator":"Robert Bala / Josh Linam","dc_status":"new","head_coach_first_season":"2026"},"Louisiana":{"record_2025":"6-7","conf_record_2025":"5-3","head_coach":"Michael Desormeaux","head_coach_status":"returning","offensive_coordinator":"Tim Leger","oc_status":"returning","defensive_coordinator":"Jim Salgado","dc_status":"returning","head_coach_first_season":"2022"},"UL-Monroe":{"record_2025":"3-9","conf_record_2025":"1-7","head_coach":"Bryant Vincent","head_coach_status":"returning","offensive_coordinator":"Jesse Montalto","oc_status":"new","defensive_coordinator":"Troy Reffett","dc_status":"new","head_coach_first_season":"2024"},"Marshall":{"record_2025":"5-7","conf_record_2025":"3-5","head_coach":"Tony Gibson","head_coach_status":"returning","offensive_coordinator":"Rod Smith","oc_status":"returning","defensive_coordinator":"Brad Lambert","dc_status":"new","head_coach_first_season":"2025"},"Old Dominion":{"record_2025":"10-3","conf_record_2025":"6-2","head_coach":"Ricky Rahne","head_coach_status":"returning","offensive_coordinator":"Kody Cook / Alex Huettel","oc_status":"new","defensive_coordinator":"Blake Seiler","dc_status":"returning","head_coach_first_season":"2020"},"South Alabama":{"record_2025":"4-8","conf_record_2025":"3-5","head_coach":"Major Applewhite","head_coach_status":"returning","offensive_coordinator":"Major Applewhite","oc_status":"new","defensive_coordinator":"Todd Orlando / Jason Washington","dc_status":"partial","head_coach_first_season":"2024"},"Southern Miss":{"record_2025":"7-6","conf_record_2025":"5-3","head_coach":"Blake Anderson","head_coach_status":"returning","offensive_coordinator":"Kyle Cefalo","oc_status":"new","defensive_coordinator":"Joe Bolden","dc_status":"new","head_coach_first_season":"2025"},"Troy":{"record_2025":"8-6","conf_record_2025":"6-2","head_coach":"Gerad Parker","head_coach_status":"returning","offensive_coordinator":"Adam Austin","oc_status":"new","defensive_coordinator":"Dontae Wright","dc_status":"partial","head_coach_first_season":"2024"}};
const coachBettingRows = DB.coach_betting || [];
const coach1hBettingRows = DB.coach_1h_betting || [];
const coach2hBettingRows = DB.coach_2h_betting || [];
const coachBettingByTeam = Object.fromEntries(coachBettingRows.map(r => [String(r.team || '').toLowerCase(), r]));
const coach1hBettingByTeam = Object.fromEntries(coach1hBettingRows.map(r => [String(r.team || '').toLowerCase(), r]));
const coach2hBettingByTeam = Object.fromEntries(coach2hBettingRows.map(r => [String(r.team || '').toLowerCase(), r]));
let coachTrendPeriod = 'game';
function currentCoachTrendRows() {
  if (coachTrendPeriod === '1h') return coach1hBettingRows;
  if (coachTrendPeriod === '2h') return coach2hBettingRows;
  return coachBettingRows;
}
function currentCoachTrendLabel() {
  if (coachTrendPeriod === '1h') return '1st Half';
  if (coachTrendPeriod === '2h') return '2nd Half';
  return 'Full Game';
}
function setCoachTrendPeriod(period) {
  coachTrendPeriod = period;
  if ((location.hash || '#/') !== '#coach-betting') location.hash = '#coach-betting';
  else route();
}
let coachSortState = {key:'ats_rank', dir:'asc'};
let coachFilterText = '';

function avg(arr) {
  return arr.length ? arr.reduce((a,b)=>a+b,0) / arr.length : null;
}
function opponentDifficultyForSOS(teamName, g) {
  const isHome = g.home_team === teamName;
  const oppName = isHome ? g.away_team : g.home_team;
  const opp = teamByName[oppName.toLowerCase()];
  const team = teamByName[teamName.toLowerCase()];
  if (!opp) return null;
  const oppCombo = Number(opp.combo);
  if (!Number.isFinite(oppCombo)) return null;
  if (g.neutral_site) return oppCombo;
  if (isHome) {
    const teamHfa = Number(team?.hfa);
    return oppCombo - (Number.isFinite(teamHfa) ? teamHfa : 0);
  }
  const oppHfa = Number(opp.hfa);
  return oppCombo + (Number.isFinite(oppHfa) ? oppHfa : 0);
}
const overallSOSByTeam = {};
const confSOSByTeam = {};
DB.teams.forEach(t => {
  const games = DB.games.filter(g => g.home_team===t.team || g.away_team===t.team);
  const overallOpps = games
    .map(g => opponentDifficultyForSOS(t.team, g))
    .filter(v => typeof v === 'number' && !Number.isNaN(v));
  const confOpps = games
    .filter(g => g.is_conference_game)
    .map(g => opponentDifficultyForSOS(t.team, g))
    .filter(v => typeof v === 'number' && !Number.isNaN(v));
  overallSOSByTeam[t.team] = avg(overallOpps);
  confSOSByTeam[t.team] = avg(confOpps);
});

const comboRankByTeam = {};
[...DB.teams]
  .sort((a,b) => (Number(b.combo) || -999) - (Number(a.combo) || -999))
  .forEach((t, i) => { comboRankByTeam[t.team] = i + 1; });

const spOffRankByTeam = {};
[...DB.teams]
  .sort((a,b) => (Number(b.sp_offense) || -999) - (Number(a.sp_offense) || -999))
  .forEach((t, i) => { spOffRankByTeam[t.team] = i + 1; });

const spDefRankByTeam = {};
[...DB.teams]
  .sort((a,b) => (Number(a.sp_defense) || 999) - (Number(b.sp_defense) || 999))
  .forEach((t, i) => { spDefRankByTeam[t.team] = i + 1; });

const hfaRankByTeam = {};
[...DB.teams]
  .sort((a,b) => (Number(b.hfa) || -999) - (Number(a.hfa) || -999))
  .forEach((t, i) => { hfaRankByTeam[t.team] = i + 1; });

const avgWinsRankByTeam = {};
[...DB.teams]
  .sort((a,b) => (Number(b.avg_total_wins) || -999) - (Number(a.avg_total_wins) || -999))
  .forEach((t, i) => { avgWinsRankByTeam[t.team] = i + 1; });

const overallSOSRankByTeam = {};
[...DB.teams]
  .sort((a,b) => (overallSOSByTeam[b.team] ?? -999) - (overallSOSByTeam[a.team] ?? -999))
  .forEach((t, i) => { overallSOSRankByTeam[t.team] = i + 1; });

const confSOSRankByTeam = {};
DB.conferences.forEach(c => {
  const ranked = [...c.teams].sort((a,b) => (confSOSByTeam[b.team] ?? -999) - (confSOSByTeam[a.team] ?? -999));
  ranked.forEach((t, i) => { confSOSRankByTeam[t.team] = i + 1; });
});

const RESULTS_STORAGE_KEY = 'ncaaf_2026_results_overrides_v1';
let scheduleViewMode = localStorage.getItem('ncaaf_2026_schedule_view_mode_v1') || 'simple';
let scheduleMarketLabMode = localStorage.getItem('ncaaf_2026_marketlab_mode_v1') || 'spreads';
let scheduleSortState = {key:'date', dir:'asc'};
function loadResultsState() {
  try {
    return JSON.parse(localStorage.getItem(RESULTS_STORAGE_KEY) || '{}');
  } catch (e) {
    return {};
  }
}
let resultsState = loadResultsState();
function saveResultsState() {
  localStorage.setItem(RESULTS_STORAGE_KEY, JSON.stringify(resultsState));
}
function embeddedGameState(g) {
  const rawStatus = String(g.cfbd_status || g.status || '').toLowerCase();
  const awayScore = g.cfbd_away_score ?? g.away_score ?? '';
  const homeScore = g.cfbd_home_score ?? g.home_score ?? '';
  const hasScore = awayScore !== '' && awayScore !== null && homeScore !== '' && homeScore !== null;
  const finalish = rawStatus.includes('final') || rawStatus.includes('completed') || g.completed === true || g.cfbd_completed === true || hasScore;
  return {
    status: finalish ? 'final' : 'scheduled',
    away_score: hasScore ? awayScore : '',
    home_score: hasScore ? homeScore : '',
    source: g.cfbd_game_id ? 'CFBD' : (finalish ? 'embedded' : 'schedule'),
    cfbd_game_id: g.cfbd_game_id || ''
  };
}
function gameState(g) {
  const base = embeddedGameState(g);
  const override = resultsState[g.game_id];
  if (!override) return base;
  return {...base, ...override, source: override.source || 'manual'};
}
function setGameState(gameId, nextState) {
  resultsState[gameId] = {...(resultsState[gameId] || {}), ...nextState, source:'manual'};
  saveResultsState();
}
function clearGameState(gameId) {
  delete resultsState[gameId];
  saveResultsState();
}
function gameStatusChip(g) {
  const st = gameState(g);
  const cls = st.status === 'final' ? 'final' : 'missing';
  const label = st.status === 'final' ? 'Final' : 'Scheduled';
  const source = st.source === 'manual' ? 'Manual' : (st.source === 'CFBD' ? 'CFBD' : 'Schedule');
  return `<span class="data-chip ${cls}${st.source === 'manual' ? ' manual' : ''}">${label}${source ? ' · '+source : ''}</span>`;
}
function gameScoreText(g) {
  const st = gameState(g);
  if (st.status !== 'final' || st.away_score === '' || st.home_score === '') return '—';
  return `${st.away_score}-${st.home_score}`;
}
function gameResultParts(g) {
  const st = gameState(g);
  const ascore = Number(st.away_score), hscore = Number(st.home_score);
  if (st.status !== 'final' || !Number.isFinite(ascore) || !Number.isFinite(hscore)) return {winner:'—', margin:'—', total:'—'};
  const winner = ascore === hscore ? 'Tie' : (ascore > hscore ? g.away_team : g.home_team);
  return {winner, margin:hscore-ascore, total:ascore+hscore};
}
function firstPresent(...vals) {
  for (const v of vals) if (v !== undefined && v !== null && v !== '') return v;
  return null;
}
function marketSpread(g) {
  return firstPresent(g.market_spread_home, g.sgo_home_spread, g.market_home_spread, g.market_spread, g.sgo_spread, g.close_spread);
}
function marketSpreadText(g) {
  return firstPresent(g.market_spread_text, g.market_formatted_spread, g.sgo_spread_text, g.formatted_spread);
}
function marketSpreadBook(g) {
  return firstPresent(g.market_spread_book, g.market_books_available, g.sgo_book, g.book);
}
function marketTotalBook(g) {
  return firstPresent(g.market_total_book, g.market_books_available, g.sgo_book, g.book);
}
function marketSpreadPrice(g) {
  return firstPresent(g.sgo_home_spread_price, g.market_home_spread_price, g.market_spread_price, g.sgo_spread_price, g.close_spread_price);
}
function marketTotal(g) {
  return firstPresent(g.market_total, g.sgo_game_total, g.sgo_total, g.close_total);
}
function marketOverPrice(g) {
  return firstPresent(
    g.market_total_over_price,
    g.market_best_over_price,
    g.sgo_over_price,
    g.market_over_price,
    g.game_over_price,
    g.close_over_price
  );
}

function marketUnderPrice(g) {
  return firstPresent(
    g.market_total_under_price,
    g.market_best_under_price,
    g.sgo_under_price,
    g.market_under_price,
    g.game_under_price,
    g.close_under_price
  );
}

function market1HSpread(g) {
  return firstPresent(g.sgo_1h_home_spread, g.sgo_home_1h_spread, g.home_1h_spread, g.market_1h_home_spread, g.one_h_home_spread, g.first_half_home_spread);
}
function market1HSpreadPrice(g) {
  return firstPresent(g.sgo_1h_home_spread_price, g.sgo_home_1h_spread_price, g.home_1h_spread_price, g.market_1h_home_spread_price, g.one_h_home_spread_price, g.first_half_home_spread_price);
}
function market1HTotal(g) {
  return firstPresent(g.sgo_1h_total, g.sgo_one_h_total, g.one_h_total, g.market_1h_total, g.first_half_total);
}
function market1HOverPrice(g) {
  return firstPresent(g.sgo_1h_over_price, g.sgo_one_h_over_price, g.one_h_over_price, g.market_1h_over_price, g.first_half_over_price);
}
function market1HUnderPrice(g) {
  return firstPresent(g.sgo_1h_under_price, g.sgo_one_h_under_price, g.one_h_under_price, g.market_1h_under_price, g.first_half_under_price);
}
function fmtAmerican(v) {
  if (v === null || v === undefined || v === '') return '';
  const s = String(v).trim();
  if (!s) return '';
  const n = Number(s);
  if (Number.isFinite(n)) return n > 0 ? `+${n}` : `${n}`;
  return s;
}
function fmtMarket(v) { return v == null || v === '' || Number.isNaN(Number(v)) ? '—' : (Number(v)>0?'+':'') + Number(v).toFixed(1); }
function marketBookSubline(g, kind='spread') {
  const book = kind === 'total' ? marketTotalBook(g) : marketSpreadBook(g);
  const source = firstPresent(g.market_line_source, g.line_source, 'Market');
  const books = firstPresent(g.market_books_available, book);
  const bits = [];
  if (source) bits.push(source);
  if (books) bits.push(books);
  return bits.length ? `<span class="line-sub">${bits.map(x => escapeHtml(String(x))).join(' · ')}</span>` : '';
}
function fmtMarketSpreadCell(g) {
  const display = marketSpreadText(g);
  const line = marketSpread(g);
  const price = fmtAmerican(marketSpreadPrice(g));

  if ((display == null || display === '') && (line == null || line === '' || Number.isNaN(Number(line)))) return '—';

  const main = display ? escapeHtml(String(display)) : fmtMarket(line);

  // Use the actual sportsbook for this selected line, not the full available-book list.
  const book = firstPresent(g.market_spread_book, g.sgo_book, g.book);
  const priceHtml = price ? `<span class="market-price-inline">${price}</span>` : '';
  const bookHtml = book ? `<span class="market-book-inline">${bookLogoBadge(book)}</span>` : '';

  return `<span class="market-line-one"><b>${main}</b>${priceHtml}${bookHtml}</span>`;
}
function fmtMarketTotalCell(g) {
  const line = marketTotal(g);
  const over = fmtAmerican(marketOverPrice(g));
  const under = fmtAmerican(marketUnderPrice(g));
  if (line == null || line === '' || Number.isNaN(Number(line))) return '—';
  const prices = [over ? `O ${over}` : '', under ? `U ${under}` : ''].filter(Boolean).join(' / ');
  return `<div class="proj-market"><span class="line-main">${Number(line).toFixed(1)}</span>${prices ? `<span class="line-sub">${prices}</span>` : ''}${marketBookSubline(g, 'total')}</div>`;
}

function cleanMarketTeamNameForDisplay(name) {
  return escapeHtml(String(name || '').trim());
}

function marketSpreadDisplayText(g) {
  const line = marketSpread(g);
  if (line == null || line === '' || Number.isNaN(Number(line))) return '';
  const n = Number(line);

  // marketSpread is home-team perspective.
  // Negative means home team favored; positive means away team favored.
  const team = n <= 0 ? g.home_team : g.away_team;
  const pts = Math.abs(n);
  const ptsText = Number.isInteger(pts) ? String(pts) : pts.toFixed(1).replace(/\.0$/, '');
  return `${team} -${ptsText}`;
}

function signedLineText(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return '';
  if (Math.abs(n) < 0.0001) return 'PK';
  return `${n > 0 ? '+' : ''}${n.toFixed(1).replace(/\.0$/,'')}`;
}


function marketSpreadHoldBadge(g) {
  const v = Number(g && g.market_spread_hold_pct);
  if (!Number.isFinite(v)) return '';
  const label = `Hold ${v >= 0 ? '+' : ''}${v.toFixed(1)}%`;
  let cls = 'market-hold-neutral';
  if (v < 0) cls = 'market-hold-arb';
  else if (v <= 2) cls = 'market-hold-low';
  else if (v >= 5) cls = 'market-hold-high';
  return `<div class="market-hold-badge ${cls}" title="Synthetic hold using the two best available spread sides. Lower is better for the bettor. Negative hold means bettor edge / arbitrage condition.">${label}</div>`;
}

function fmtMarketSideLine(team, lineForTeam, price, book) {
  const lineTxt = signedLineText(lineForTeam);
  const priceTxt = fmtAmerican(price);
  const teamLogo = teamImageImg(team);
  const bookBadge = book ? sportsbookLogo(book) : '';
  if (!team || !lineTxt) return '';
  return `<div class="market-side-line">${teamLogo}<b>${escapeHtml(String(team))} ${lineTxt}</b>${priceTxt ? ` <span class="muted">${priceTxt}</span>` : ''}${bookBadge}</div>`;
}


/* COACH_HALVES_FRONT_EDGE_START */
function coachHalfRowForTeam(team, half) {
  const key = half === '2h' ? 'coach_2h_betting' : 'coach_1h_betting';
  const rows = (DB && DB[key]) || [];
  const target = typeof normName === 'function' ? normName(team) : String(team || '').toLowerCase().trim();
  return rows.find(r => {
    const vals = [r.team, r.current_team, r.Team, r["Current Team"]];
    return vals.some(v => {
      const n = typeof normName === 'function' ? normName(v) : String(v || '').toLowerCase().trim();
      return n && n === target;
    });
  }) || null;
}

function coachHalfNum(row, keys) {
  if (!row) return null;
  for (const k of keys) {
    const n = Number(row[k]);
    if (Number.isFinite(n)) return n;
  }
  return null;
}

function coachHalfRecord(row) {
  if (!row) return 'No data';
  if (row.ats_record) return row.ats_record;
  const w = coachHalfNum(row, ['ats_w']);
  const l = coachHalfNum(row, ['ats_l']);
  const p = coachHalfNum(row, ['ats_push']);
  if (w == null || l == null) return 'No data';
  return `${w}-${l}-${p || 0}`;
}

function coachHalfPct(row) {
  const pct = coachHalfNum(row, ['ats_pct','ats_win_pct','ats_win']);
  return pct == null ? '—' : `${(pct * 100).toFixed(1)}%`;
}

function coachHalfMargin(row) {
  return coachHalfNum(row, ['ats_margin','ats_plus_minus','avg_ats','avg_cover_margin','cover_margin']);
}

function coachHalfRank(row) {
  return coachHalfNum(row, ['ats_rank']);
}

function coachHalfScore(row) {
  if (!row) return null;
  const margin = coachHalfMargin(row);
  const pct = coachHalfNum(row, ['ats_pct','ats_win_pct','ats_win']);
  const games = coachHalfNum(row, ['ats_games','games']) || 0;
  const rank = coachHalfRank(row);

  let score = 0;
  if (margin != null) score += margin;
  if (pct != null) score += (pct - 0.5) * 20;
  score += Math.min(3, games / 10);
  if (rank != null) score += Math.max(0, (70 - rank) / 20);
  return score;
}

function coachHalfEdgeForGame(g, half) {
  const away = coachHalfRowForTeam(g.away_team, half);
  const home = coachHalfRowForTeam(g.home_team, half);
  const awayScore = coachHalfScore(away);
  const homeScore = coachHalfScore(home);

  // Do not manufacture an edge when either side is missing data.
  if (awayScore == null || homeScore == null) {
    return {half, away, home, edgeTeam:null, diff:null, signedDiff:null, noData:true};
  }

  const diff = homeScore - awayScore;
  const edgeTeam = diff >= 0 ? g.home_team : g.away_team;
  return {half, away, home, edgeTeam, diff:Math.abs(diff), signedDiff:diff, noData:false};
}

function coachHalfEdgeSummary(g) {
  const h1 = coachHalfEdgeForGame(g, '1h');
  const h2 = coachHalfEdgeForGame(g, '2h');
  const candidates = [h1, h2].filter(x => x.edgeTeam && Number.isFinite(x.diff));
  if (!candidates.length) return {best:null, h1, h2};
  candidates.sort((a,b) => b.diff - a.diff);
  return {best:candidates[0], h1, h2};
}

function coachHalfMiniLine(label, row) {
  if (!row) return `${label}: No data`;
  const margin = coachHalfMargin(row);
  const rank = coachHalfRank(row);
  const rankTxt = rank != null ? ` #${rank}` : '';
  const marginTxt = margin == null ? '—' : `${margin >= 0 ? '+' : ''}${margin.toFixed(1)}`;
  return `${label}: ${coachHalfRecord(row)}${rankTxt} · ${coachHalfPct(row)} · ${marginTxt}`;
}


/* COACH_GRADE_DISPLAY_HELPERS_START */
function coachDisplayGrade(score, games, kind='ats') {
  const s = Number(score);
  const g = Number(games);
  if (!Number.isFinite(s) || !Number.isFinite(g) || g < 8) {
    return {grade:'—', cls:'muted', label:'No grade'};
  }

  let grade = 'C';
  if (g >= 20 && s >= 6) grade = 'A';
  else if (s >= 2.5) grade = 'B';
  else if (s <= -3) grade = 'D';

  const cls = grade === 'A' ? 'edge-pos'
    : grade === 'B' ? 'chip-warn'
    : grade === 'D' ? 'edge-neg'
    : 'muted';

  const sample = g >= 25 ? 'Strong sample' : g >= 15 ? 'Medium sample' : 'Thin sample';
  return {grade, cls, label:sample};
}

function coachGradeBadge(gradeObj) {
  if (!gradeObj || !gradeObj.grade || gradeObj.grade === '—') {
    return `<span class="coach-grade-badge muted" title="No grade">—</span>`;
  }
  return `<span class="coach-grade-badge ${gradeObj.cls}" title="${escapeHtml(gradeObj.label || '')}">${gradeObj.grade}</span>`;
}

function coachRowForEdgeTeam(g, half, team) {
  const row = coachHalfRowForTeam(team, half);
  return row || null;
}

function coachShortTeamName(team) {
  return String(team || '')
    .replace('State', 'St')
    .replace('University', '')
    .replace(/\s+/g, ' ')
    .trim();
}
/* COACH_GRADE_DISPLAY_HELPERS_END */


function fmtCoachHalfEdgeCell(g) {
  const s = coachHalfEdgeSummary(g);
  if (!s.best || !Number.isFinite(s.best.diff)) return '<span class="muted">—</span>';

  const bestLabel = s.best.half === '1h' ? '1H' : '2H';
  const team = String(s.best.edgeTeam || '');
  const shortTeam = coachShortTeamName(team);
  const row = coachRowForEdgeTeam(g, s.best.half, team);
  const games = coachHalfNum(row, ['ats_games','games']) || 0;
  const score = coachHalfScore(row);
  const gradeObj = coachDisplayGrade(score, games, 'ats');

  const sampleTxt = typeof coachSampleLabel === 'function' ? coachSampleLabel(games) : `${games} games`;
  const title = row
    ? `${bestLabel} ${team}: ${coachHalfRecord(row)} ATS · ${coachHalfPct(row)} · ${sampleTxt}`
    : `${bestLabel} ${team}: no coach ATS data`;

  return `<span class="coach-half-edge-cell ${gradeObj.cls}" title="${escapeHtml(title)}">${bestLabel} ${escapeHtml(shortTeam)} ${coachGradeBadge(gradeObj)}</span>`;
}

function matchupCoachHalvesCard(g) {
  const s = coachHalfEdgeSummary(g);
  const away1 = coachHalfRowForTeam(g.away_team, '1h');
  const home1 = coachHalfRowForTeam(g.home_team, '1h');
  const away2 = coachHalfRowForTeam(g.away_team, '2h');
  const home2 = coachHalfRowForTeam(g.home_team, '2h');

  const best = s.best
    ? `<span class="edge-pos">${s.best.half === '1h' ? '1H' : '2H'}: ${escapeHtml(s.best.edgeTeam)} +${s.best.diff.toFixed(1)}</span>`
    : '<span class="muted">No clear coach-half edge</span>';

  return `<div class="card coach-halves-front-card">
    <div class="section-title">Coach Halves Betting Edge</div>
    <div class="small" style="margin-bottom:10px">Current 2026 coach history from refreshed SGO 1H/2H ATS records through 2026-01-20.</div>
    <div class="coach-half-best">Best coach-half lean: ${best}</div>
    <div class="coach-half-grid">
      <div>
        <div class="kpi">1st Half</div>
        <div class="small"><b>${escapeHtml(g.away_team)}</b> — ${escapeHtml(coachHalfMiniLine('', away1).replace(/^: /,''))}</div>
        <div class="small"><b>${escapeHtml(g.home_team)}</b> — ${escapeHtml(coachHalfMiniLine('', home1).replace(/^: /,''))}</div>
      </div>
      <div>
        <div class="kpi">2nd Half</div>
        <div class="small"><b>${escapeHtml(g.away_team)}</b> — ${escapeHtml(coachHalfMiniLine('', away2).replace(/^: /,''))}</div>
        <div class="small"><b>${escapeHtml(g.home_team)}</b> — ${escapeHtml(coachHalfMiniLine('', home2).replace(/^: /,''))}</div>
      </div>
    </div>
  </div>`;
}
/* COACH_HALVES_FRONT_EDGE_END */

function fmtMarketSpreadCompactCell(g) {
  const homeLine = firstPresent(g.market_best_home_spread_home, g.market_spread_home);
  const homePrice = firstPresent(g.market_best_home_spread_price, g.market_spread_price);
  const homeBook = firstPresent(g.market_best_home_spread_book, g.market_spread_book);

  const awayHomePerspective = firstPresent(g.market_best_away_spread_home, g.market_spread_home);
  const awayLine = awayHomePerspective == null || awayHomePerspective === '' ? null : -Number(awayHomePerspective);
  const awayPrice = firstPresent(g.market_best_away_spread_price, g.market_spread_price);
  const awayBook = firstPresent(g.market_best_away_spread_book, g.market_spread_book);

  const homeHtml = fmtMarketSideLine(g.home_team, homeLine, homePrice, homeBook);
  const awayHtml = fmtMarketSideLine(g.away_team, awayLine, awayPrice, awayBook);
  const holdHtml = marketSpreadHoldBadge(g);

  if (!homeHtml && !awayHtml) return '—';
  return `<div class="market-spread-two-side">${homeHtml}${awayHtml}${holdHtml}</div>`;
}


function fmtMarketTotalTwoSideCell(g) {
  if (isKnownBadTotalMarket(g)) return '—';

  const overTotal = firstPresent(g.market_best_over_total, g.market_total);
  const overPrice = firstPresent(g.market_best_over_price, marketOverPrice(g));
  const overBook = firstPresent(g.market_best_over_book, g.market_total_book);

  const underTotal = firstPresent(g.market_best_under_total, g.market_total);
  const underPrice = firstPresent(g.market_best_under_price, marketUnderPrice(g));
  const underBook = firstPresent(g.market_best_under_book, g.market_total_book);

  function totalLine(side, total, price, book) {
    if (!hasActualTotalMarket(total, price, book)) return '';
    const totalTxt = Number(total).toFixed(1).replace(/\.0$/,'');
    const priceTxt = fmtAmerican(price);
    return `<div class="market-side-line market-total-line"><b>${side} ${totalTxt}</b> <span class="muted">${priceTxt}</span>${sportsbookLogo(book)}</div>`;
  }

  const overLine = totalLine('Over', overTotal, overPrice, overBook);
  const underLine = totalLine('Under', underTotal, underPrice, underBook);

  const lines = [overLine, underLine].filter(Boolean).join('');
  return lines ? `<div class="market-spread-two-side market-total-two-side">${lines}</div>` : '—';
}

function fmtMarketTotalCompactCell(g) {
  const line = marketTotal(g);
  if (line == null || line === '' || Number.isNaN(Number(line))) return '—';
  const over = fmtAmerican(marketOverPrice(g));
  const under = fmtAmerican(marketUnderPrice(g));
  const priceText = [over ? `O ${over}` : '', under ? `U ${under}` : ''].filter(Boolean).join(' / ');
  return `<span class="nowrap"><b>${Number(line).toFixed(1)}</b>${priceText ? ` <span class="muted">(${priceText})</span>` : ''}</span>`;
}
function fmtMarket1HSpreadCell(g) {
  const line = market1HSpread(g);
  const price = fmtAmerican(market1HSpreadPrice(g));
  if (line == null || line === '' || Number.isNaN(Number(line))) return '—';
  return `<div class="proj-market"><span class="line-main">${fmtMarket(line)}</span>${price ? `<span class="line-sub">${price}</span>` : ''}</div>`;
}
function fmtMarket1HTotalCell(g) {
  const line = market1HTotal(g);
  const over = fmtAmerican(market1HOverPrice(g));
  const under = fmtAmerican(market1HUnderPrice(g));
  if (line == null || line === '' || Number.isNaN(Number(line))) return '—';
  const prices = [over ? `O ${over}` : '', under ? `U ${under}` : ''].filter(Boolean).join(' / ');
  return `<div class="proj-market"><span class="line-main">${Number(line).toFixed(1)}</span>${prices ? `<span class="line-sub">${prices}</span>` : ''}</div>`;
}
function fmtEdge(v) { return v == null || Number.isNaN(v) ? '—' : `<span class="${v>=0?'edge-pos':'edge-neg'}">${v>0?'+':''}${v.toFixed(1)}</span>`; }
function normalCdf(x) {
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x) / Math.sqrt(2);
  const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741, a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
  const t = 1 / (1 + p * x);
  const y = 1 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*Math.exp(-x*x);
  return 0.5 * (1 + sign*y);
}
function americanToDecimal(odds) {
  const o = Number(odds);
  if (!Number.isFinite(o) || o === 0) return 1.9090909;
  return o > 0 ? 1 + o / 100 : 1 + 100 / Math.abs(o);
}
function evFromProbAndOdds(prob, odds=-110) {
  if (!Number.isFinite(prob)) return null;
  const dec = americanToDecimal(odds);
  return prob * (dec - 1) - (1 - prob);
}
function defaultPrice(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : -110;
}
function priceStatusText(v) {
  const n = Number(v);
  return Number.isFinite(n) && n !== 0 ? fmtAmerican(n) : '-110 assumed';
}
  function numOrNull(v) {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }

  function genericAtsEdgeValue(g) {
    const ms = marketSpread(g);
    if (ms == null || ms === '' || Number.isNaN(Number(ms))) return null;
    return Number(g.projected_margin_home) + Number(ms);
  }

  function bestAtsMarketForSide(g, side) {
    if (side === 'home') {
      const bestLine = firstPresent(g.market_best_home_spread_home, g.market_spread_home);
      const bestPrice = firstPresent(g.market_best_home_spread_price, g.market_spread_price);
      const bestBook = firstPresent(g.market_best_home_spread_book, g.market_spread_book);
      return {line:numOrNull(bestLine), price:bestPrice, book:bestBook, side:'home'};
    }

    const bestLine = firstPresent(g.market_best_away_spread_home, g.market_spread_home);
    const bestPrice = firstPresent(g.market_best_away_spread_price, g.market_spread_price);
    const bestBook = firstPresent(g.market_best_away_spread_book, g.market_spread_book);
    return {line:numOrNull(bestLine), price:bestPrice, book:bestBook, side:'away'};
  }

  function bestAtsMarket(g) {
    const genericEdge = genericAtsEdgeValue(g);
    if (genericEdge == null) return {edge:null, line:null, price:null, book:null, side:null};

    const side = genericEdge >= 0 ? 'home' : 'away';
    const m = bestAtsMarketForSide(g, side);
    if (m.line == null) return {edge:genericEdge, line:null, price:null, book:null, side};

    return {
      ...m,
      edge: Number(g.projected_margin_home) + Number(m.line)
    };
  }

  function atsEdgeValue(g) {
    return bestAtsMarket(g).edge;
  }

  function genericTotalEdgeValue(g) {
    const mt = marketTotal(g);
    if (mt == null || mt === '' || Number.isNaN(Number(mt))) return null;
    return Number(g.projected_total) - Number(mt);
  }

  function isKnownBadTotalMarket(g) {
  const away = String(g && g.away_team || '').toLowerCase().trim();
  const home = String(g && g.home_team || '').toLowerCase().trim();

  // Action Network/FanDuel false total: this total is not actually posted yet.
  if (away === 'north alabama' && home === 'arkansas') return true;

  return false;
}

function hasActualTotalMarket(total, price, book) {
  if (total == null || total === '' || Number.isNaN(Number(total))) return false;
  if (price == null || price === '' || Number.isNaN(Number(price))) return false;
  if (book == null || String(book).trim() === '') return false;
  return true;
}

function bestTotalMarket(g) {
  if (isKnownBadTotalMarket(g)) return {edge:null, total:null, price:null, book:null, side:null};

  const genericEdge = genericTotalEdgeValue(g);
  if (genericEdge == null) return {edge:null, total:null, price:null, book:null, side:null};

  const overTotal = firstPresent(g.market_best_over_total, g.market_total);
  const overPrice = firstPresent(g.market_best_over_price, marketOverPrice(g));
  const overBook = firstPresent(g.market_best_over_book, g.market_total_book);

  const underTotal = firstPresent(g.market_best_under_total, g.market_total);
  const underPrice = firstPresent(g.market_best_under_price, marketUnderPrice(g));
  const underBook = firstPresent(g.market_best_under_book, g.market_total_book);

  const hasOver = hasActualTotalMarket(overTotal, overPrice, overBook);
  const hasUnder = hasActualTotalMarket(underTotal, underPrice, underBook);

  if (genericEdge >= 0) {
    if (!hasOver) return {edge:null, total:null, price:null, book:null, side:'Over'};
    const n = numOrNull(overTotal);
    return {side:'Over', total:n, price:overPrice, book:overBook, edge:Number(g.projected_total) - n};
  }

  if (!hasUnder) return {edge:null, total:null, price:null, book:null, side:'Under'};
  const n = numOrNull(underTotal);
  return {side:'Under', total:n, price:underPrice, book:underBook, edge:Number(g.projected_total) - n};
}

function totalEdgeValue(g) {
    return bestTotalMarket(g).edge;
  }
function atsModelProb(edge) {
  if (edge == null || Number.isNaN(edge)) return null;
  return normalCdf(Math.abs(edge) / 14);
}
function totalModelProb(edge) {
  if (edge == null || Number.isNaN(edge)) return null;
  return normalCdf(Math.abs(edge) / 17);
}
function betScore(edge, evPct, booksCount=1) {
  if (evPct == null || Number.isNaN(evPct) || edge == null || Number.isNaN(edge)) return null;
  const score = 50 + (Number(evPct) * 2.0) + (Math.abs(Number(edge)) * 2.5) + Math.min(5, Math.max(0, Number(booksCount || 1) - 1) * 1.5);
  return Math.max(0, Math.min(100, score));
}
function fmtEvPct(v) {
  if (v == null || Number.isNaN(v)) return '—';
  return `<span class="${v>=0?'edge-pos':'edge-neg'}">${v>=0?'+':''}${v.toFixed(1)}%</span>`;
}
function fmtBetScore(v) {
  if (v == null || Number.isNaN(v)) return '—';
  const cls = v >= 80 ? 'edge-pos' : v >= 70 ? 'chip-warn' : v >= 60 ? 'muted' : 'edge-neg';
  return `<span class="${cls}">${v.toFixed(0)}</span>`;
}
function fmtAtsValueSide(g, edge) {
  if (edge == null || Number.isNaN(edge)) return '—';
  const side = edge >= 0 ? g.home_team : g.away_team;
  return `<span class="${Math.abs(edge)>=1?'edge-pos':'muted'}">${escapeHtml(side)} +${Math.abs(edge).toFixed(1)}</span>`;
}
function fmtTotalValueSide(edge) {
  if (edge == null || Number.isNaN(edge)) return '—';
  const side = edge >= 0 ? 'Over' : 'Under';
  return `<span class="${Math.abs(edge)>=1?'edge-pos':'muted'}">${side} +${Math.abs(edge).toFixed(1)}</span>`;
}
  function fmtBookMini(book) {
    return book ? ` · ${escapeHtml(String(book))}` : '';
  }

  function fmtAtsSideWithCoachHalf(g, atsSideHtml) {
  const coach = fmtCoachHalfEdgeCell(g);
  if (!coach || coach.includes('muted') || coach.includes('—')) return atsSideHtml;
  return `<div class="ats-edge-with-coach">
    <div>${atsSideHtml}</div>
    <div class="ats-coach-half-support">Coach: ${coach}</div>
  </div>`;
}

function marketLabAtsMetrics(g) {
  const m = bestAtsMarket(g);
  const edge = m.edge;
  if (edge == null) return {side:'—', ev:'—', score:'—'};
  const prob = atsModelProb(edge);
  const rawPrice = m.price;
  const price = defaultPrice(rawPrice);
  const evPct = evFromProbAndOdds(prob, price) * 100;
  const sideTeam = m.side === 'home' ? g.home_team : g.away_team;
  const cls = Math.abs(edge) >= 1 ? 'edge-pos' : 'muted';
  const logo = teamImageImg(sideTeam);

  return {
    side: `<span class="market-ats-edge-side nowrap ${cls}">${logo}<span>${escapeHtml(sideTeam)} +${Math.abs(edge).toFixed(1)}</span></span>`,
    ev: fmtEvPct(evPct),
    score: fmtBetScore(betScore(edge, evPct, g.market_books_count))
  };
}


/* COACH_TOTALS_INLINE_SUPPORT_START */
function coachHalfTotalRecord(row) {
  if (!row) return 'No data';
  if (row.ou_record) return row.ou_record;
  if (row.over_under_record) return row.over_under_record;
  const o = coachHalfNum(row, ['overs']);
  const u = coachHalfNum(row, ['unders']);
  const p = coachHalfNum(row, ['total_push']);
  if (o == null || u == null) return 'No data';
  return `${o}-${u}-${p || 0}`;
}

function coachHalfTotalMargin(row) {
  return coachHalfNum(row, ['total_margin','avg_total_margin','avg_total']);
}

function coachHalfOverPct(row) {
  return coachHalfNum(row, ['over_pct','over']);
}

function coachHalfTotalScore(row, side) {
  if (!row) return null;
  const overPct = coachHalfOverPct(row);
  const margin = coachHalfTotalMargin(row);
  const games = coachHalfNum(row, ['over_games','games']) || 0;
  if (overPct == null && margin == null) return null;

  let score = 0;
  if (margin != null) score += side === 'Over' ? margin : -margin;
  if (overPct != null) score += side === 'Over' ? (overPct - 0.5) * 20 : (0.5 - overPct) * 20;
  score += Math.min(3, games / 10);
  return score;
}

function coachTotalSupportForGame(g, totalSide) {
  const rows = [
    {half:'1H', team:g.away_team, row:coachHalfRowForTeam(g.away_team, '1h')},
    {half:'1H', team:g.home_team, row:coachHalfRowForTeam(g.home_team, '1h')},
    {half:'2H', team:g.away_team, row:coachHalfRowForTeam(g.away_team, '2h')},
    {half:'2H', team:g.home_team, row:coachHalfRowForTeam(g.home_team, '2h')},
  ];

  const scored = rows.map(x => ({...x, score:coachHalfTotalScore(x.row, totalSide)}))
    .filter(x => Number.isFinite(x.score));

  if (!scored.length) return null;
  scored.sort((a,b) => b.score - a.score);
  return scored[0];
}

function fmtCoachTotalSupportCell(g, totalSide) {
  const best = coachTotalSupportForGame(g, totalSide);
  if (!best) return '';

  const games = coachHalfNum(best.row, ['over_games','games']) || 0;
  const gradeObj = coachDisplayGrade(best.score, games, 'total');
  const shortTeam = coachShortTeamName(best.team);

  const rec = coachHalfTotalRecord(best.row);
  const overPct = coachHalfOverPct(best.row);
  const margin = coachHalfTotalMargin(best.row);
  const overPctTxt = overPct == null ? '—' : `${(overPct * 100).toFixed(1)}% Over`;
  const marginTxt = margin == null ? '—' : `${margin >= 0 ? '+' : ''}${margin.toFixed(1)}`;

  const title = `Coach half total trend: ${best.half} ${totalSide} ${best.team} · ${rec} · ${overPctTxt} · Total +/- ${marginTxt}`;

  return `<div class="total-coach-support ${gradeObj.cls}" title="${escapeHtml(title)}">
    Coach O/U: ${best.half} ${escapeHtml(totalSide)} ${escapeHtml(shortTeam)} ${coachGradeBadge(gradeObj)}
  </div>`;
}

function fmtTotalSideWithCoachHalf(g, totalSideHtml) {
  let side = null;
  try {
    const m = bestTotalMarket(g);
    side = m && m.side ? m.side : null;
  } catch(e) {}

  if (!side) {
    const edge = totalEdgeValue(g);
    if (edge != null && Number.isFinite(Number(edge))) side = Number(edge) >= 0 ? 'Over' : 'Under';
  }

  if (!side) return totalSideHtml;

  const coach = fmtCoachTotalSupportCell(g, side);
  if (!coach) return totalSideHtml;

  return `<div class="total-edge-with-coach">
    <div>${totalSideHtml}</div>
    ${coach}
  </div>`;
}
/* COACH_TOTALS_INLINE_SUPPORT_END */


function marketLabTotalMetrics(g) {
  const m = bestTotalMarket(g);
  const edge = m.edge;
  if (edge == null) return {side:'—', ev:'—', score:'—'};

  const prob = totalModelProb(edge);
  const rawPrice = m.price;
  const price = defaultPrice(rawPrice);
  const evPct = evFromProbAndOdds(prob, price) * 100;

  const side = m.side || (edge >= 0 ? 'Over' : 'Under');
  const cls = Math.abs(edge) >= 1 ? 'edge-pos' : 'muted';

  return {
    side: `<span class="nowrap market-total-edge-side ${cls}">${escapeHtml(side)} +${Math.abs(edge).toFixed(1)}</span>`,
    ev: fmtEvPct(evPct),
    score: fmtBetScore(betScore(edge, evPct, g.market_books_count))
  };
}

function setMarketLabMode(mode) {
  scheduleMarketLabMode = mode === 'totals' ? 'totals' : 'spreads';
  localStorage.setItem('ncaaf_2026_marketlab_mode_v1', scheduleMarketLabMode);

  const toggle = document.getElementById('marketLabSubToggle');
  if (toggle) {
    toggle.querySelectorAll('button').forEach(btn => {
      const txt = String(btn.textContent || '').trim().toLowerCase();
      btn.classList.toggle('active', txt === scheduleMarketLabMode || (scheduleMarketLabMode === 'spreads' && txt === 'spreads') || (scheduleMarketLabMode === 'totals' && txt === 'totals'));
    });
  }

  mountScheduleFilters();
}

function setScheduleViewMode(mode) {
  scheduleViewMode = mode;
  localStorage.setItem('ncaaf_2026_schedule_view_mode_v1', mode);
  const wrap = byId('scheduleWrap');
  if (wrap) mountScheduleFilters();
}
function getResultsSummary() {
  const finals = DB.games.filter(g => gameState(g).status === 'final');
  const teamStats = {};
  DB.teams.forEach(t => teamStats[t.team] = {wins:0, losses:0, conf_wins:0, conf_losses:0, pf:0, pa:0});
  finals.forEach(g => {
    const st = gameState(g);
    const ascore = Number(st.away_score);
    const hscore = Number(st.home_score);
    if (!Number.isFinite(ascore) || !Number.isFinite(hscore) || ascore === hscore) return;
    const away = teamStats[g.away_team], home = teamStats[g.home_team];
    away.pf += ascore; away.pa += hscore;
    home.pf += hscore; home.pa += ascore;
    const awayWin = ascore > hscore;
    if (awayWin) { away.wins++; home.losses++; } else { home.wins++; away.losses++; }
    if (g.is_conference_game) {
      if (awayWin) { away.conf_wins++; home.conf_losses++; } else { home.conf_wins++; away.conf_losses++; }
    }
  });
  return {finals, teamStats};
}
function exportResultsJson() {
  return JSON.stringify(resultsState, null, 2);
}
function importResultsJson(text) {
  const parsed = JSON.parse(text);
  if (!parsed || typeof parsed !== 'object') throw new Error('Invalid JSON');
  resultsState = parsed;
  saveResultsState();
}

const BETTING_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTmGvvkdhjSorHoTPbW5f33N6--AXLmWBLitZomgKejjOpo2aG6bL4UFtVfD3RFteCUNPEbDilnq2X1/pubhtml?gid=938568824&single=true";
const BETTING_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTmGvvkdhjSorHoTPbW5f33N6--AXLmWBLitZomgKejjOpo2aG6bL4UFtVfD3RFteCUNPEbDilnq2X1/pub?gid=938568824&single=true&output=csv";
const BETTING_ROWS = [{"Date": "3/14/2025", "Account": "James", "Bet Description": "Win Total", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Iowa state under 5.5", "Bet Type": "Total", "Bet Line": 5.5, "Bet Price": -115.0, "Result": "", "Profit": -57.5, "Running Profit": -57.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "3/14/2025", "Account": "James", "Bet Description": "Win Total", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Auburn under 6.5", "Bet Type": "Total", "Bet Line": 6.5, "Bet Price": -110.0, "Result": "", "Profit": -55, "Running Profit": -112.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "3/14/2025", "Account": "James", "Bet Description": "Win Total", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 65.0, "Sport": "NCAAF", "Bet": "Georgia tech under 6.5", "Bet Type": "Total", "Bet Line": 6.5, "Bet Price": -130.0, "Result": "", "Profit": -65, "Running Profit": -177.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "3/14/2025", "Account": "James", "Bet Description": "Win Total", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 70.0, "Sport": "NCAAF", "Bet": "Colorado under 4.5", "Bet Type": "Total", "Bet Line": 4.5, "Bet Price": -140.0, "Result": "", "Profit": -70, "Running Profit": -247.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "3/14/2025", "Account": "James", "Bet Description": "Win Total", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 79.0, "Sport": "NCAAF", "Bet": "Ohio state over 9.5", "Bet Type": "Total", "Bet Line": 9.5, "Bet Price": -158.0, "Result": "", "Profit": -79, "Running Profit": -326.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "3/14/2025", "Account": "James", "Bet Description": "Win Total", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 69.0, "Sport": "NCAAF", "Bet": "Georgia over 9.5", "Bet Type": "Total", "Bet Line": 9.5, "Bet Price": -138.0, "Result": "", "Profit": -69, "Running Profit": -395.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "3/14/2025", "Account": "James", "Bet Description": "Win Total", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 70.0, "Sport": "NCAAF", "Bet": "Ole miss over 7.5", "Bet Type": "Total", "Bet Line": 7.5, "Bet Price": -140.0, "Result": "", "Profit": -70, "Running Profit": -465.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "3/14/2025", "Account": "James", "Bet Description": "Conf Title", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 70.0, "Sport": "NCAAF", "Bet": "Oregon win B10", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 300.0, "Result": "", "Profit": -70, "Running Profit": -535.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "3/14/2025", "Account": "James", "Bet Description": "Conf Title", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 50.0, "Sport": "NCAAF", "Bet": "Georgia win SEC", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 390.0, "Result": "", "Profit": -50, "Running Profit": -585.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "3/14/2025", "Account": "James", "Bet Description": "Conf Title", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 25.0, "Sport": "NCAAF", "Bet": "SMU win ACC", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 700.0, "Result": "", "Profit": -25, "Running Profit": -610.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "3/14/2025", "Account": "James", "Bet Description": "Conf Title", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 115.0, "Sport": "NCAAF", "Bet": "Texas tech win big 12", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": -115.0, "Result": "", "Profit": -115, "Running Profit": -725.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}];
const BETTING_2025_ROWS = [{"Date": "8/14/2025", "Account": "James", "Bet Description": "", "Source": "Tunes", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NFL", "Bet": "Raiders ", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -57.5, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/14/2025", "Account": "James", "Bet Description": "", "Source": "powers", "Sportsbook": "Fan Duel", "Bet Amount": 65.0, "Sport": "NFL", "Bet": "seahwaks", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -158.0, "Result": "Win", "Profit": 41.13924051, "Running Profit": -16.36075949, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/14/2025", "Account": "James", "Bet Description": "", "Source": "Clevta", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NFL", "Bet": "Tenn/atl under ", "Bet Type": "Total", "Bet Line": 37.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -73.86075949, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/14/2025", "Account": "James", "Bet Description": "", "Source": "Clevta", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NFL", "Bet": "Kc/sea under ", "Bet Type": "Total", "Bet Line": 39.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -131.3607595, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/1/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fanatics", "Bet Amount": 28.0, "Sport": "NCAAF", "Bet": "Penn st ", "Bet Type": "Side", "Bet Line": -42.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -28, "Running Profit": -159.3607595, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/4/2025", "Account": "Ashlee", "Bet Description": "", "Source": "Powers", "Sportsbook": "Bet365", "Bet Amount": 200.0, "Sport": "NCAAF", "Bet": "Ohio st/tex under ", "Bet Type": "Total", "Bet Line": 50.5, "Bet Price": -110.0, "Result": "Win", "Profit": 181.8181818, "Running Profit": 22.45742232, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/11/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 13.0, "Sport": "NCAAF", "Bet": "Miami/ND under ", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -105.0, "Result": "Win", "Profit": 12.38095238, "Running Profit": 34.83837471, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/11/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 150.0, "Sport": "NCAAF", "Bet": "Miami/ND under ", "Bet Type": "Total", "Bet Line": 51.5, "Bet Price": -110.0, "Result": "Win", "Profit": 136.3636364, "Running Profit": 171.2020111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/12/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 150.0, "Sport": "NCAAF", "Bet": "Tennessee/cuse under ", "Bet Type": "Total", "Bet Line": 51.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -150, "Running Profit": 21.20201107, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/21/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 110.0, "Sport": "NCAAF", "Bet": "Kansas", "Bet Type": "Side", "Bet Line": -12.5, "Bet Price": -110.0, "Result": "Win", "Profit": 100, "Running Profit": 121.2020111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/21/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 52.0, "Sport": "NFL", "Bet": "Steelers/giants", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -105.0, "Result": "Win", "Profit": 49.52380952, "Running Profit": 170.7258206, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/21/2025", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "kst/iowa st 1st H under", "Bet Type": "Total", "Bet Line": 25.5, "Bet Price": -122.0, "Result": "Win", "Profit": 49.18032787, "Running Profit": 219.9061485, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/21/2025", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Prime", "Bet Amount": 53.5, "Sport": "NCAAF", "Bet": "wky/shst under", "Bet Type": "Total", "Bet Line": 62.0, "Bet Price": -107.0, "Result": "Loss", "Profit": -53.5, "Running Profit": 166.4061485, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/22/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Unlv", "Bet Type": "Side", "Bet Line": -26.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -55, "Running Profit": 111.4061485, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/23/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 22.0, "Sport": "NCAAF", "Bet": "Nc central ", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -110.0, "Result": "Win", "Profit": 20, "Running Profit": 131.4061485, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/23/2025", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Draft Kings", "Bet Amount": 30.0, "Sport": "NCAAF", "Bet": "kst/iowa st 1st H under", "Bet Type": "Total", "Bet Line": 24.5, "Bet Price": 130.0, "Result": "Win", "Profit": 39, "Running Profit": 170.4061485, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/23/2025", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NCAAF", "Bet": "kst/iowa st 1st H under", "Bet Type": "Total", "Bet Line": 26.5, "Bet Price": 121.0, "Result": "Win", "Profit": 12.1, "Running Profit": 182.5061485, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/23/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Caesers", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Stanford", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 110.0, "Result": "Loss", "Profit": -20, "Running Profit": 162.5061485, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/23/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 33.0, "Sport": "NCAAF", "Bet": "Unlv/shst under ", "Bet Type": "Total", "Bet Line": 61.5, "Bet Price": -115.0, "Result": "Win", "Profit": 28.69565217, "Running Profit": 191.2018006, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/23/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 128.0, "Sport": "NCAAF", "Bet": "Arizona", "Bet Type": "Side", "Bet Line": -14.0, "Bet Price": -110.0, "Result": "Win", "Profit": 116.3636364, "Running Profit": 307.565437, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/23/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Arizona ", "Bet Type": "Side", "Bet Line": -14.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 357.565437, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/25/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 41.0, "Sport": "NCAAF", "Bet": "nc state", "Bet Type": "Side", "Bet Line": -11.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -41, "Running Profit": 316.565437, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/25/2025", "Account": "Ashlee", "Bet Description": "", "Source": "Powers", "Sportsbook": "Bet365", "Bet Amount": 110.0, "Sport": "NCAAF", "Bet": "Alabama", "Bet Type": "Side", "Bet Line": -8.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -110, "Running Profit": 206.565437, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/27/2025", "Account": "James", "Bet Description": "", "Source": "JAF", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "utah/ucla under", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": 149.065437, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/28/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 11.0, "Sport": "NCAAF", "Bet": "San Jose st ", "Bet Type": "Side", "Bet Line": -11.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -11, "Running Profit": 138.065437, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/28/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 44.0, "Sport": "NCAAF", "Bet": "San Jose st ", "Bet Type": "Side", "Bet Line": -11.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -44, "Running Profit": 94.065437, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/28/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 44.4, "Sport": "NCAAF", "Bet": "Boise/usf over ", "Bet Type": "Total", "Bet Line": 62.0, "Bet Price": -111.0, "Result": "Loss", "Profit": -44.4, "Running Profit": 49.665437, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/28/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 58.0, "Sport": "NCAAF", "Bet": "nebraska", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -116.0, "Result": "Loss", "Profit": -58, "Running Profit": -8.334563001, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/28/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 135.0, "Sport": "NCAAF", "Bet": "rutgers TT over", "Bet Type": "Total", "Bet Line": 32.5, "Bet Price": -135.0, "Result": "Win", "Profit": 100, "Running Profit": 91.665437, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/28/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 130.0, "Sport": "NCAAF", "Bet": "rutgers TT over", "Bet Type": "Total", "Bet Line": 33.5, "Bet Price": -130.0, "Result": "Win", "Profit": 100, "Running Profit": 191.665437, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/28/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 162.0, "Sport": "NCAAF", "Bet": "rutgers TT over", "Bet Type": "Total", "Bet Line": 32.5, "Bet Price": -140.0, "Result": "Win", "Profit": 115.7142857, "Running Profit": 307.3797227, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/29/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 220.0, "Sport": "NCAAF", "Bet": "Army ", "Bet Type": "Side", "Bet Line": -13.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -220, "Running Profit": 87.37972271, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/29/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 114.0, "Sport": "NCAAF", "Bet": "Shst TT over ", "Bet Type": "Total", "Bet Line": 25.5, "Bet Price": -114.0, "Result": "Loss", "Profit": -114, "Running Profit": -26.62027729, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/29/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 136.0, "Sport": "NCAAF", "Bet": "Shst TT over ", "Bet Type": "Total", "Bet Line": 25.5, "Bet Price": -116.0, "Result": "Loss", "Profit": -136, "Running Profit": -162.6202773, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/29/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 43.0, "Sport": "NCAAF", "Bet": "Shst TT over ", "Bet Type": "Total", "Bet Line": 24.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -43, "Running Profit": -205.6202773, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/29/2025", "Account": "James", "Bet Description": "", "Source": "Bonus bet", "Sportsbook": "Caesers", "Bet Amount": 75.0, "Sport": "NCAAF", "Bet": "Syracuse", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 400.0, "Result": "Loss", "Profit": -75, "Running Profit": -280.6202773, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/29/2025", "Account": "James", "Bet Description": "", "Source": "Bonus hedge ", "Sportsbook": "Fan Duel", "Bet Amount": 250.0, "Sport": "NCAAF", "Bet": "Tennessee", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -500.0, "Result": "Win", "Profit": 50, "Running Profit": -230.6202773, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/29/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Georgia tech ", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -106.0, "Result": "Win", "Profit": 18.86792453, "Running Profit": -211.7523528, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/29/2025", "Account": "James", "Bet Description": "", "Source": "powers", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "miami ", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": 111.0, "Result": "Win", "Profit": 22.2, "Running Profit": -189.5523528, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/29/2025", "Account": "James", "Bet Description": "", "Source": "powers", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "miami", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -112.0, "Result": "Win", "Profit": 17.85714286, "Running Profit": -171.6952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/29/2025", "Account": "James", "Bet Description": "", "Source": "powers", "Sportsbook": "Hard Rock", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "miami", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -120.0, "Result": "Win", "Profit": 50, "Running Profit": -121.6952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "powers", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Tcu/unc under ", "Bet Type": "Total", "Bet Line": 55.5, "Bet Price": 130.0, "Result": "Loss", "Profit": -20, "Running Profit": -141.6952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "powers", "Sportsbook": "Fan Duel", "Bet Amount": 15.0, "Sport": "NCAAF", "Bet": "Tcu/unc under ", "Bet Type": "Total", "Bet Line": 55.6, "Bet Price": 120.0, "Result": "Loss", "Profit": -15, "Running Profit": -156.6952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/7/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 270.0, "Sport": "NFL", "Bet": "Eagles/Broncos", "Bet Type": "Parlay", "Bet Line": "-1/-1.5", "Bet Price": -135.0, "Result": "Win", "Profit": 200, "Running Profit": 43.3047901, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/2/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Hurts TD", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 150.0, "Result": "Win", "Profit": 30, "Running Profit": 73.3047901, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Prime", "Bet Amount": 59.0, "Sport": "NCAAF", "Bet": "SMU", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -118.0, "Result": "Loss", "Profit": -59, "Running Profit": 14.3047901, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 52.0, "Sport": "NCAAF", "Bet": "jacksonville st", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -104.0, "Result": "Win", "Profit": 50, "Running Profit": 64.3047901, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "ole miss", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 9.304790099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Prime", "Bet Amount": 53.5, "Sport": "NCAAF", "Bet": "cincinnati ", "Bet Type": "Side", "Bet Line": -17.5, "Bet Price": -107.0, "Result": "Loss", "Profit": -53.5, "Running Profit": -44.1952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Prime", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Memphis", "Bet Type": "Side", "Bet Line": -13.0, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 5.804790099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "BYU", "Bet Type": "Side", "Bet Line": -17.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 55.8047901, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Fan Duel", "Bet Amount": 53.0, "Sport": "NCAAF", "Bet": "BYU", "Bet Type": "Side", "Bet Line": -20.5, "Bet Price": -106.0, "Result": "Win", "Profit": 50, "Running Profit": 105.8047901, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 11.0, "Sport": "NCAAF", "Bet": "Oklahoma", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -110.0, "Result": "Win", "Profit": 10, "Running Profit": 115.8047901, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 44.0, "Sport": "NCAAF", "Bet": "Oklahoma", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -110.0, "Result": "Win", "Profit": 40, "Running Profit": 155.8047901, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "powers", "Sportsbook": "Fan Duel", "Bet Amount": 150.0, "Sport": "NCAAF", "Bet": "Cincinnati", "Bet Type": "Side", "Bet Line": -19.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -150, "Running Profit": 5.804790099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "powers", "Sportsbook": "Fan Duel", "Bet Amount": 200.0, "Sport": "NCAAF", "Bet": "Michigan state", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -120.0, "Result": "Loss", "Profit": -200, "Running Profit": -194.1952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "powers", "Sportsbook": "Hard Rock", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Michigan state ", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -55, "Running Profit": -249.1952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Troy", "Bet Type": "Side", "Bet Line": 33.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -199.1952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Ole miss/kent 1H under ", "Bet Type": "Total", "Bet Line": 26.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -256.6952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 175.0, "Sport": "NCAAF", "Bet": "Ole miss/kent 1H under ", "Bet Type": "Total", "Bet Line": 26.5, "Bet Price": -122.0, "Result": "Loss", "Profit": -175, "Running Profit": -431.6952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 52.0, "Sport": "NCAAF", "Bet": "kent state", "Bet Type": "Side", "Bet Line": 48.5, "Bet Price": -104.0, "Result": "Win", "Profit": 50, "Running Profit": -381.6952099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "MGM", "Bet Amount": 27.47, "Sport": "NCAAF", "Bet": "duke/ill 1H Under", "Bet Type": "Total", "Bet Line": 24.5, "Bet Price": -118.0, "Result": "Loss", "Profit": -27.47, "Running Profit": -409.1652099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Prime", "Bet Amount": 27.0, "Sport": "NCAAF", "Bet": "duke/ill 1H Under", "Bet Type": "Total", "Bet Line": 24.0, "Bet Price": -108.0, "Result": "Loss", "Profit": -27, "Running Profit": -436.1652099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Prime", "Bet Amount": 58.5, "Sport": "NCAAF", "Bet": "ucla/unlv over", "Bet Type": "Total", "Bet Line": 54.5, "Bet Price": -117.0, "Result": "Loss", "Profit": -58.5, "Running Profit": -494.6652099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 58.0, "Sport": "NCAAF", "Bet": "fresno/oregon st 1H Under", "Bet Type": "Total", "Bet Line": 23.5, "Bet Price": -122.0, "Result": "Loss", "Profit": -58, "Running Profit": -552.6652099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "MGM", "Bet Amount": 25.6, "Sport": "NCAAF", "Bet": "Florida 1H", "Bet Type": "Side", "Bet Line": -10.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -25.6, "Running Profit": -578.2652099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Caesers", "Bet Amount": 22.0, "Sport": "NCAAF", "Bet": "Florida 1H", "Bet Type": "Side", "Bet Line": -10.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -22, "Running Profit": -600.2652099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Hard Rock", "Bet Amount": 11.5, "Sport": "NCAAF", "Bet": "Tulsa", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -11.5, "Running Profit": -611.7652099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Hard Rock", "Bet Amount": 10.5, "Sport": "NCAAF", "Bet": "Tulsa", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -10.5, "Running Profit": -622.2652099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "MGM", "Bet Amount": 33.0, "Sport": "NCAAF", "Bet": "Tulsa", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -33, "Running Profit": -655.2652099, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Caesers", "Bet Amount": 10.0, "Sport": "NCAAF", "Bet": "Michigan/Oklahoma 1H under", "Bet Type": "Total", "Bet Line": 23.0, "Bet Price": -114.0, "Result": "Win", "Profit": 8.771929825, "Running Profit": -646.4932801, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Western Kentucky", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -703.9932801, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 65.0, "Sport": "NFL", "Bet": "Herbert Over 14.5 rush yds", "Bet Type": "Total", "Bet Line": 14.5, "Bet Price": -135.0, "Result": "Win", "Profit": 48.14814815, "Running Profit": -655.8451319, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "MGM", "Bet Amount": 125.0, "Sport": "NCAAF", "Bet": "UNI/Maryland under", "Bet Type": "Total", "Bet Line": 46.5, "Bet Price": -125.0, "Result": "Win", "Profit": 100, "Running Profit": -555.8451319, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 270.0, "Sport": "NFL", "Bet": "Seahawks/falcons", "Bet Type": "Parlay", "Bet Line": 7.5, "Bet Price": -135.0, "Result": "Win", "Profit": 200, "Running Profit": -355.8451319, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Hard Rock", "Bet Amount": 28.75, "Sport": "NCAAF", "Bet": "Miami OH", "Bet Type": "Side", "Bet Line": 14.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -28.75, "Running Profit": -384.5951319, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/1/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 220.0, "Sport": "NCAAF", "Bet": "Baylor", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -118.0, "Result": "Win", "Profit": 186.440678, "Running Profit": -198.154454, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Baylor ", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -115.0, "Result": "Win", "Profit": 47.82608696, "Running Profit": -150.328367, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 43.0, "Sport": "NCAAF", "Bet": "Oregon 1st half ", "Bet Type": "Side", "Bet Line": -16.5, "Bet Price": -118.0, "Result": "Win", "Profit": 36.44067797, "Running Profit": -113.887689, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 118.0, "Sport": "NCAAF", "Bet": "Oregon 1st half ", "Bet Type": "Side", "Bet Line": -17.0, "Bet Price": -110.0, "Result": "Win", "Profit": 107.2727273, "Running Profit": -6.614961767, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 40.0, "Sport": "NCAAF", "Bet": "Michigan ", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -107.0, "Result": "Loss", "Profit": -40, "Running Profit": -46.61496177, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 130.0, "Sport": "NFL", "Bet": "Lions/Bears", "Bet Type": "Parlay", "Bet Line": 7.5, "Bet Price": -130.0, "Result": "Loss", "Profit": -130, "Running Profit": -176.6149618, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Giants", "Bet Type": "Side", "Bet Line": 6.0, "Bet Price": 139.0, "Result": "Loss", "Profit": -20, "Running Profit": -196.6149618, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 80.0, "Sport": "NFL", "Bet": "Giants", "Bet Type": "Side", "Bet Line": 6.0, "Bet Price": -108.0, "Result": "Loss", "Profit": -80, "Running Profit": -276.6149618, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/7/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Oregon/NW Under", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -226.6149618, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/7/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Colo/Houston Over", "Bet Type": "Total", "Bet Line": 43.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -176.6149618, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/7/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Georgia Tech", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -126.6149618, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/7/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Tennessee", "Bet Type": "Side", "Bet Line": 7.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -76.61496177, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "South Florida", "Bet Type": "Side", "Bet Line": 16.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -131.6149618, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "USF/Miami Over", "Bet Type": "Total", "Bet Line": 53.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -81.61496177, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "Tulane", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -122.0, "Result": "Win", "Profit": 49.18032787, "Running Profit": -32.4346339, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Temple", "Bet Type": "Side", "Bet Line": 28.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -87.4346339, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Arizona", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -37.4346339, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "jacksonville st", "Bet Type": "Side", "Bet Line": 6.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -92.4346339, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 58.0, "Sport": "NCAAF", "Bet": "east carolina", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -116.0, "Result": "Win", "Profit": 50, "Running Profit": -42.4346339, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 110.0, "Sport": "NCAAF", "Bet": "East Carolina", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -115.0, "Result": "Win", "Profit": 95.65217391, "Running Profit": 53.21754002, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 12.0, "Sport": "", "Bet": "East Carolina ", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -120.0, "Result": "Win", "Profit": 10, "Running Profit": 63.21754002, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Tunes", "Sportsbook": "Hard Rock", "Bet Amount": 38.5, "Sport": "NFL", "Bet": "Lions", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -110.0, "Result": "Win", "Profit": 35, "Running Profit": 98.21754002, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 220.0, "Sport": "NFL", "Bet": "texans", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -220, "Running Profit": -121.78246, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 300.0, "Sport": "NCAAF", "Bet": "georgia southern", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -162.0, "Result": "Win", "Profit": 185.1851852, "Running Profit": 63.4027252, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Hard Rock", "Bet Amount": 26.25, "Sport": "NCAAF", "Bet": "Houston", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -105.0, "Result": "Win", "Profit": 25, "Running Profit": 88.4027252, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Hard Rock", "Bet Amount": 26.25, "Sport": "NCAAF", "Bet": "Memphis", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -105.0, "Result": "Win", "Profit": 25, "Running Profit": 113.4027252, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Hard Rock", "Bet Amount": 25.0, "Sport": "NCAAF", "Bet": "Houston ", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -115.0, "Result": "Win", "Profit": 21.73913043, "Running Profit": 135.1418556, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Nc state", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -133.0, "Result": "Win", "Profit": 15.03759398, "Running Profit": 150.1794496, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NCAAF", "Bet": "Nc state", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 228.0, "Result": "Win", "Profit": 22.8, "Running Profit": 172.9794496, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 23.0, "Sport": "NCAAF", "Bet": "ucla/new mexico over", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -23, "Running Profit": 149.9794496, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 270.0, "Sport": "NFL", "Bet": "colts/chiefs", "Bet Type": "Parlay", "Bet Line": 7.5, "Bet Price": -135.0, "Result": "Win", "Profit": 200, "Running Profit": 349.9794496, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 165.0, "Sport": "NCAAF", "Bet": "wazzu/ntex under", "Bet Type": "Total", "Bet Line": 57.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -165, "Running Profit": 184.9794496, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 64.4, "Sport": "NCAAF", "Bet": "wazzu/ntex under", "Bet Type": "Total", "Bet Line": 57.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -64.4, "Running Profit": 120.5794496, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Powers", "Sportsbook": "Bet365", "Bet Amount": 165.0, "Sport": "NCAAF", "Bet": "Houston", "Bet Type": "Side", "Bet Line": -4.0, "Bet Price": -115.0, "Result": "Win", "Profit": 143.4782609, "Running Profit": 264.0577105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "MGM", "Bet Amount": 110.0, "Sport": "NCAAF", "Bet": "iowa state", "Bet Type": "Side", "Bet Line": -21.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -110, "Running Profit": 154.0577105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "MGM", "Bet Amount": 75.0, "Sport": "NCAAF", "Bet": "Buffalo", "Bet Type": "Side", "Bet Line": -22.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -75, "Running Profit": 79.05771049, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Hard Rock", "Bet Amount": 33.0, "Sport": "NCAAF", "Bet": "Buffalo", "Bet Type": "Side", "Bet Line": -21.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -33, "Running Profit": 46.05771049, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Hard Rock", "Bet Amount": 27.5, "Sport": "NCAAF", "Bet": "Boston College", "Bet Type": "Side", "Bet Line": -13.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -27.5, "Running Profit": 18.55771049, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "MGM", "Bet Amount": 110.0, "Sport": "NCAAF", "Bet": "Boston College", "Bet Type": "Side", "Bet Line": -13.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -110, "Running Profit": -91.44228951, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "morgan state", "Bet Type": "Side", "Bet Line": 35.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -146.4422895, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 22.0, "Sport": "NCAAF", "Bet": "Holy cross", "Bet Type": "", "Bet Line": 4.5, "Bet Price": -110.0, "Result": "Win", "Profit": 20, "Running Profit": -126.4422895, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 25.0, "Sport": "NCAAF", "Bet": "New Hampshire", "Bet Type": "", "Bet Line": 3.5, "Bet Price": -118.0, "Result": "Loss", "Profit": -25, "Running Profit": -151.4422895, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 27.0, "Sport": "NCAAF", "Bet": "Eastern Kentucky ", "Bet Type": "", "Bet Line": 14.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -27, "Running Profit": -178.4422895, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 44.0, "Sport": "NCAAF", "Bet": "Texas A&M TT O21.5", "Bet Type": "", "Bet Line": 21.5, "Bet Price": -112.0, "Result": "Win", "Profit": 39.28571429, "Running Profit": -139.1565752, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NCAAF", "Bet": "Texas A&M TT O21.5", "Bet Type": "", "Bet Line": 21.5, "Bet Price": 117.0, "Result": "Win", "Profit": 11.7, "Running Profit": -127.4565752, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 30.0, "Sport": "NCAAF", "Bet": "Texas A&M TT O21.5", "Bet Type": "", "Bet Line": 21.5, "Bet Price": 136.0, "Result": "Win", "Profit": 40.8, "Running Profit": -86.65657522, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 110.0, "Sport": "NCAAF", "Bet": "Texas A&M TT O21.5", "Bet Type": "", "Bet Line": 21.5, "Bet Price": -110.0, "Result": "Win", "Profit": 100, "Running Profit": 13.34342478, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/14/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "USC", "Bet Type": "Side", "Bet Line": -13.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 63.34342478, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/14/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Ucf", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 113.3434248, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/14/2025", "Account": "James", "Bet Description": "", "Source": "CLEVTA", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NFL", "Bet": "Judkins over 11.5 yards ", "Bet Type": "Total", "Bet Line": 11.5, "Bet Price": -118.0, "Result": "Win", "Profit": 50.84745763, "Running Profit": 164.1908824, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/14/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Utah", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": 106.6908824, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/14/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Temple/GT over", "Bet Type": "Total", "Bet Line": 49.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 156.6908824, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/14/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 110.0, "Sport": "NFL", "Bet": "Jets", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -110, "Running Profit": 46.6908824, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/14/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Prime", "Bet Amount": 54.5, "Sport": "NCAAF", "Bet": "Louisiana ", "Bet Type": "Side", "Bet Line": -3.0, "Bet Price": -109.0, "Result": "Loss", "Profit": -54.5, "Running Profit": -7.809117598, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "9/14/2025", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Prime", "Bet Amount": 53.5, "Sport": "NCAAF", "Bet": "Liberty", "Bet Type": "Side", "Bet Line": 11.5, "Bet Price": -107.0, "Result": "Loss", "Profit": -53.5, "Running Profit": -61.3091176, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Prime", "Bet Amount": 56.5, "Sport": "NCAAF", "Bet": "Louisiana Tech", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -113.0, "Result": "Win", "Profit": 50, "Running Profit": -11.3091176, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "Purdue", "Bet Type": "Side", "Bet Line": 27.5, "Bet Price": -112.0, "Result": "Win", "Profit": 50, "Running Profit": 38.6908824, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 100.0, "Sport": "NCAAF", "Bet": "Duke ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -140.0, "Result": "Win", "Profit": 71.42857143, "Running Profit": 110.1194538, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 135.0, "Sport": "NCAAF", "Bet": "Duke", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Win", "Profit": 117.3913043, "Running Profit": 227.5107582, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 135.0, "Sport": "NCAAF", "Bet": "Miami OH", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -115.0, "Result": "Win", "Profit": 117.3913043, "Running Profit": 344.9020625, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 110.0, "Sport": "NCAAF", "Bet": "Miami OH", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -110.0, "Result": "Win", "Profit": 100, "Running Profit": 444.9020625, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 225.0, "Sport": "NCAAF", "Bet": "Purdue/ND Over", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -112.0, "Result": "Win", "Profit": 200.8928571, "Running Profit": 645.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Powers", "Sportsbook": "Bet365", "Bet Amount": 230.0, "Sport": "NFL", "Bet": "Rams", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -230, "Running Profit": 415.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 220.0, "Sport": "NFL", "Bet": "Browns", "Bet Type": "Side", "Bet Line": 8.5, "Bet Price": -110.0, "Result": "Win", "Profit": 200, "Running Profit": 615.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Bonus Bet", "Sportsbook": "MGM", "Bet Amount": 200.0, "Sport": "NFL", "Bet": "Browns", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 350.0, "Result": "Win", "Profit": 700, "Running Profit": 1315.79492, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Bonus Bet", "Sportsbook": "Bet365", "Bet Amount": 570.0, "Sport": "NFL", "Bet": "Packers", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -425.0, "Result": "Loss", "Profit": -570, "Running Profit": 745.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Prime", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Virginia 1H", "Bet Type": "Side", "Bet Line": -8.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 795.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Usc/msu over ", "Bet Type": "Total", "Bet Line": 55.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 845.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Prime", "Bet Amount": 56.5, "Sport": "NCAAF", "Bet": "Miami/florida 1H under ", "Bet Type": "Total", "Bet Line": 26.0, "Bet Price": -113.0, "Result": "Win", "Profit": 50, "Running Profit": 895.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Rutgers/Iowa under ", "Bet Type": "Total", "Bet Line": 47.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 840.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Prime", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "ULL/EMU under ", "Bet Type": "Total", "Bet Line": 51.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": 783.2949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Draft Kings", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Georgia state ", "Bet Type": "Side", "Bet Line": 28.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": 725.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "ClevTA", "Sportsbook": "Hard Rock", "Bet Amount": 55.0, "Sport": "NFL", "Bet": "Dolphins TT O18.5", "Bet Type": "Total", "Bet Line": 18.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 775.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "ClevTA", "Sportsbook": "Draft Kings", "Bet Amount": 30.0, "Sport": "NFL", "Bet": "Dolphins ", "Bet Type": "Side", "Bet Line": 14.5, "Bet Price": -100.0, "Result": "Win", "Profit": 30, "Running Profit": 805.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 27.5, "Sport": "NCAAF", "Bet": "Northern Illinois", "Bet Type": "Side", "Bet Line": 23.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -27.5, "Running Profit": 778.2949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 26.5, "Sport": "NCAAF", "Bet": "Northern Illinois", "Bet Type": "Side", "Bet Line": 22.0, "Bet Price": -106.0, "Result": "Loss", "Profit": -26.5, "Running Profit": 751.7949197, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "Western Michigan ", "Bet Type": "Side", "Bet Line": 14.0, "Bet Price": -112.0, "Result": "Win", "Profit": 205.3571429, "Running Profit": 957.1520625, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Tunes ", "Sportsbook": "MGM", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Uab", "Bet Type": "Side", "Bet Line": 39.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 1007.152063, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 200.0, "Sport": "NFL", "Bet": "Jets", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": 100.0, "Result": "Win", "Profit": 200, "Running Profit": 1207.152063, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 130.0, "Sport": "NFL", "Bet": "Houston/denver", "Bet Type": "Parlay", "Bet Line": "7.5/9", "Bet Price": -130.0, "Result": "Win", "Profit": 100, "Running Profit": 1307.152063, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 135.0, "Sport": "NFL", "Bet": "Houston/denver", "Bet Type": "Parlay", "Bet Line": "7.5/8.5", "Bet Price": -135.0, "Result": "Win", "Profit": 100, "Running Profit": 1407.152063, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "MGM", "Bet Amount": 57.5, "Sport": "NFL", "Bet": "San Fran", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": 1349.652063, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Draft Kings", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Memphis", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 1399.652063, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Missouri", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 1344.652063, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "washington", "Bet Type": "Side", "Bet Line": -19.5, "Bet Price": -112.0, "Result": "Win", "Profit": 53.57142857, "Running Profit": 1398.223491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Cal", "Bet Type": "Side", "Bet Line": -13.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 1343.223491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Bet365", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Cal", "Bet Type": "Side", "Bet Line": -13.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -55, "Running Profit": 1288.223491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Draft Kings", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Alabama", "Bet Type": "Side", "Bet Line": 4.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 1338.223491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Oregon", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 1388.223491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Arkansas", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 1333.223491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "Pitt", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -52.5, "Running Profit": 1280.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 54.0, "Sport": "NCAAF", "Bet": "Cuse", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -108.0, "Result": "Loss", "Profit": -54, "Running Profit": 1226.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 59.0, "Sport": "NCAAF", "Bet": "Auburn", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -118.0, "Result": "Win", "Profit": 50, "Running Profit": 1276.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "ohio state", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 1326.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "pitt/louisville over", "Bet Type": "Total", "Bet Line": 53.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 1376.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "BYU", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 1321.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "ECU", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -125.0, "Result": "Win", "Profit": 48, "Running Profit": 1369.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "Arizona", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -120.0, "Result": "Loss", "Profit": -60, "Running Profit": 1309.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "gasouth/jmu over", "Bet Type": "Total", "Bet Line": 50.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 1254.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "miss st", "Bet Type": "Side", "Bet Line": 11.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 1304.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "ole miss", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 1354.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 54.0, "Sport": "NCAAF", "Bet": "UCF", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -108.0, "Result": "Loss", "Profit": -54, "Running Profit": 1300.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Virginia", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 1350.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 230.0, "Sport": "NFL", "Bet": "Vikings", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -230, "Running Profit": 1120.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 130.0, "Sport": "NFL", "Bet": "Falcons/Broncos", "Bet Type": "Parlay", "Bet Line": "7.5/-1", "Bet Price": -130.0, "Result": "Win", "Profit": 100, "Running Profit": 1220.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Powers", "Sportsbook": "Bet365", "Bet Amount": 120.0, "Sport": "NFL", "Bet": "Falcons/Broncos", "Bet Type": "Parlay", "Bet Line": "7.5/-1.5", "Bet Price": -120.0, "Result": "Win", "Profit": 100, "Running Profit": 1320.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Gt/wf over ", "Bet Type": "Total", "Bet Line": 50.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 1370.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 210.0, "Sport": "NCAAF", "Bet": "Illinois 1st H", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -105.0, "Result": "Win", "Profit": 200, "Running Profit": 1570.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 130.0, "Sport": "NCAAF", "Bet": "UTEP", "Bet Type": "Side", "Bet Line": 4.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -130, "Running Profit": 1440.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 100.0, "Sport": "NCAAF", "Bet": "UTEP", "Bet Type": "Side", "Bet Line": 4.5, "Bet Price": -120.0, "Result": "Loss", "Profit": -100, "Running Profit": 1340.723491, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NFL", "Bet": "Ari/sea 1H under ", "Bet Type": "Total", "Bet Line": 21.5, "Bet Price": -106.0, "Result": "Win", "Profit": 56.60377358, "Running Profit": 1397.327265, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Powers", "Sportsbook": "Bet365", "Bet Amount": 220.0, "Sport": "NCAAF", "Bet": "Florida Atlantic", "Bet Type": "Side", "Bet Line": 14.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -220, "Running Profit": 1177.327265, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NFL", "Bet": "49ers/jags under", "Bet Type": "Total", "Bet Line": 47.0, "Bet Price": -110.0, "Result": "", "Profit": 0.0, "Running Profit": 1177.327265, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Arizona ", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": 1119.827265, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "UCF", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": 1062.327265, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Marshall ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -102.0, "Result": "Loss", "Profit": -55, "Running Profit": 1007.327265, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "MGM", "Bet Amount": 110.0, "Sport": "NCAAF", "Bet": "Texas A&M", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -110, "Running Profit": 897.3272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "MGM", "Bet Amount": 115.0, "Sport": "NCAAF", "Bet": "Ohio state / Washington over ", "Bet Type": "Total", "Bet Line": 51.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -115, "Running Profit": 782.3272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Kansas / cincy  under ", "Bet Type": "Total", "Bet Line": 57.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": 724.8272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 27.5, "Sport": "NCAAF", "Bet": "Virginia tech ", "Bet Type": "Side", "Bet Line": 10.5, "Bet Price": -110.0, "Result": "Win", "Profit": 25, "Running Profit": 749.8272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "Arkansas Over TT29.5", "Bet Type": "Total", "Bet Line": 29.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -230, "Running Profit": 519.8272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 115.0, "Sport": "NCAAF", "Bet": "FAU Over TT 23.5", "Bet Type": "Total", "Bet Line": 23.5, "Bet Price": -115.0, "Result": "Win", "Profit": 100, "Running Profit": 619.8272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "NDST", "Bet Type": "Side", "Bet Line": -21.5, "Bet Price": -115.0, "Result": "Win", "Profit": 200, "Running Profit": 819.8272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 30.0, "Sport": "NCAAF", "Bet": "FAU", "Bet Type": "Side", "Bet Line": 14.5, "Bet Price": 103.0, "Result": "Loss", "Profit": -30, "Running Profit": 789.8272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 30.0, "Sport": "NCAAF", "Bet": "BYU", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -103.0, "Result": "Loss", "Profit": -30, "Running Profit": 759.8272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 50.0, "Sport": "NCAAF", "Bet": "alabama/georgia under", "Bet Type": "Total", "Bet Line": 66.5, "Bet Price": 120.0, "Result": "Win", "Profit": 60, "Running Profit": 819.8272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Florida State", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 869.8272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.0, "Sport": "NCAAF", "Bet": "Nebraska", "Bet Type": "Side", "Bet Line": -11.5, "Bet Price": -114.0, "Result": "Loss", "Profit": -57, "Running Profit": 812.8272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "virginia tech", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -52.5, "Running Profit": 760.3272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "notre dame", "Bet Type": "Side", "Bet Line": -15.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 810.3272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Illinois", "Bet Type": "Side", "Bet Line": -8.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 860.3272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "ohio state", "Bet Type": "Side", "Bet Line": -21.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 910.3272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Virginia", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 960.3272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Sdst over ", "Bet Type": "Total", "Bet Line": 41.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 1010.327265, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "western michigan", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 1060.327265, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "old dominion", "Bet Type": "Side", "Bet Line": -16.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 1110.327265, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "navy", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 1055.327265, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "Fresno state ", "Bet Type": "Side", "Bet Line": -13.5, "Bet Price": -112.0, "Result": "Loss", "Profit": -56, "Running Profit": 999.3272647, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 237.0, "Sport": "NCAAF", "Bet": "Cincy", "Bet Type": "Side", "Bet Line": 1.5, "Bet Price": -118.0, "Result": "Win", "Profit": 200.8474576, "Running Profit": 1200.174722, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 115.0, "Sport": "NCAAF", "Bet": "Louisville", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -115, "Running Profit": 1085.174722, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 106.0, "Sport": "NCAAF", "Bet": "Louisville", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -106.0, "Result": "Loss", "Profit": -106, "Running Profit": 979.1747223, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 118.0, "Sport": "NCAAF", "Bet": "Alabama", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -118.0, "Result": "Win", "Profit": 100, "Running Profit": 1079.174722, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 118.0, "Sport": "NCAAF", "Bet": "alabama", "Bet Type": "Side", "Bet Line": -10.0, "Bet Price": -118.0, "Result": "Win", "Profit": 100, "Running Profit": 1179.174722, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "tcu/colorado under", "Bet Type": "Total", "Bet Line": 59.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 1229.174722, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "FAU/Rice over", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": 1171.674722, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 125.0, "Sport": "NFL", "Bet": "Rams/bills", "Bet Type": "Parlay", "Bet Line": "-2.5/-2", "Bet Price": -125.0, "Result": "Loss", "Profit": -125, "Running Profit": 1046.674722, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 130.0, "Sport": "NFL", "Bet": "Rams/bills", "Bet Type": "Parlay", "Bet Line": "-2.5/-1.5", "Bet Price": -130.0, "Result": "Loss", "Profit": -130, "Running Profit": 916.6747223, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "shst/nmst under", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 966.6747223, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Navy/Air Force under", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": 909.1747223, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Troy/USA over", "Bet Type": "Total", "Bet Line": 46.5, "Bet Price": -114.0, "Result": "Win", "Profit": 48.24561404, "Running Profit": 957.4203363, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 28.0, "Sport": "NCAAF", "Bet": "charlotte/usf over", "Bet Type": "Total", "Bet Line": 54.5, "Bet Price": -115.0, "Result": "Win", "Profit": 24.34782609, "Running Profit": 981.7681624, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "Boston College", "Bet Type": "Side", "Bet Line": 7.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -230, "Running Profit": 751.7681624, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "Kansas state", "Bet Type": "Side", "Bet Line": 6.0, "Bet Price": -112.0, "Result": "Win", "Profit": 205.3571429, "Running Profit": 957.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "boise state", "Bet Type": "Side", "Bet Line": 21.0, "Bet Price": -115.0, "Result": "", "Profit": 0.0, "Running Profit": 957.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "clemson/unc over", "Bet Type": "Total", "Bet Line": 46.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 1007.125305, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Hard Rock", "Bet Amount": 43.0, "Sport": "NFL", "Bet": "ravens under 41", "Bet Type": "Total", "Bet Line": 41.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -43, "Running Profit": 964.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "MGM", "Bet Amount": 65.0, "Sport": "NCAAF", "Bet": "navy -12.5", "Bet Type": "Side", "Bet Line": -12.5, "Bet Price": -130.0, "Result": "Loss", "Profit": -65, "Running Profit": 899.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Draft Kings", "Bet Amount": 112.0, "Sport": "NCAAF", "Bet": "central michigan", "Bet Type": "", "Bet Line": -7.5, "Bet Price": -112.0, "Result": "Loss", "Profit": -112, "Running Profit": 787.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Bet365", "Bet Amount": 110.0, "Sport": "NCAAF", "Bet": "niu/miami U39", "Bet Type": "Total", "Bet Line": 38.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -110, "Running Profit": 677.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Hard Rock", "Bet Amount": 28.0, "Sport": "NFL", "Bet": "arizona under 42", "Bet Type": "Total", "Bet Line": 42.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -28, "Running Profit": 649.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 225.0, "Sport": "NCAAF", "Bet": "California ", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -112.0, "Result": "Loss", "Profit": -225, "Running Profit": 424.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 210.0, "Sport": "NFL", "Bet": "Seattle", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -210, "Running Profit": 214.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "East carolina", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 264.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "LT", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 209.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Iowa ", "Bet Type": "Side", "Bet Line": -1.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 259.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 110.0, "Sport": "NCAAF", "Bet": "Iowa/wisc over", "Bet Type": "Side", "Bet Line": -37.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -110, "Running Profit": 149.1253053, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 105.0, "Sport": "NCAAF", "Bet": "Texas A&m/ Florida over", "Bet Type": "Total", "Bet Line": 45.5, "Bet Price": -108.0, "Result": "Win", "Profit": 97.22222222, "Running Profit": 246.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open ", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "Utah", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -112.0, "Result": "Win", "Profit": 50, "Running Profit": 296.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "Oklahoma", "Bet Type": "Total", "Bet Line": 3.5, "Bet Price": -112.0, "Result": "Loss", "Profit": -56, "Running Profit": 240.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "BYU", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -125.0, "Result": "Win", "Profit": 48, "Running Profit": 288.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "SDST", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 338.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "LSU", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 388.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "fresno", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 333.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "jax st", "Bet Type": "Side", "Bet Line": -8.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 278.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Alabama/missouri under ", "Bet Type": "Total", "Bet Line": 54.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 328.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Usc/mich over", "Bet Type": "Total", "Bet Line": 54.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 273.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "UCF/cincy under ", "Bet Type": "Total", "Bet Line": 54.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": 323.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 40.0, "Sport": "NCAAF", "Bet": "Missouri state", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -125.0, "Result": "Win", "Profit": 32, "Running Profit": 355.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Missouri state over", "Bet Type": "Total", "Bet Line": 49.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": 300.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Powers", "Sportsbook": "Bet365", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "utah state", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -230, "Running Profit": 70.34752751, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 240.0, "Sport": "NFL", "Bet": "seattle", "Bet Type": "Side", "Bet Line": 1.5, "Bet Price": -120.0, "Result": "Win", "Profit": 200, "Running Profit": 270.3475275, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Draft Kings", "Bet Amount": 172.5, "Sport": "NCAAF", "Bet": "Oregon", "Bet Type": "Side", "Bet Line": -7.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -172.5, "Running Profit": 97.84752751, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Oregon", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": 112.0, "Result": "Loss", "Profit": -20, "Running Profit": 77.84752751, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Powers", "Sportsbook": "Bet365", "Bet Amount": 34.5, "Sport": "NCAAF", "Bet": "Oregon", "Bet Type": "Side", "Bet Line": -7.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -34.5, "Running Profit": 43.34752751, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "Powers", "Sportsbook": "Bet365", "Bet Amount": 33.0, "Sport": "NCAAF", "Bet": "Florida", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -33, "Running Profit": 10.34752751, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 200.0, "Sport": "NCAAF", "Bet": "Florida", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -108.0, "Result": "Loss", "Profit": -200, "Running Profit": -189.6524725, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse ", "Sportsbook": "Prime", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "Miami/akron under ", "Bet Type": "Total", "Bet Line": 47.0, "Bet Price": -121.0, "Result": "Win", "Profit": 49.58677686, "Running Profit": -140.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse ", "Sportsbook": "Prime", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "San Jose st", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -114.0, "Result": "Loss", "Profit": -60, "Running Profit": -200.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse ", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Iowa state", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -255.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Tunes", "Sportsbook": "Hard Rock", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "Iowa State", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -120.0, "Result": "Loss", "Profit": -60, "Running Profit": -315.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse ", "Sportsbook": "Prime", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "Michigan ", "Bet Type": "Side", "Bet Line": 2.5, "Bet Price": 100.0, "Result": "Loss", "Profit": -60, "Running Profit": -375.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "South Florida ", "Bet Type": "Side", "Bet Line": 2.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -325.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 236.0, "Sport": "NCAAF", "Bet": "NCSTATE", "Bet Type": "Side", "Bet Line": 24.5, "Bet Price": -118.0, "Result": "Loss", "Profit": -236, "Running Profit": -561.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 105.0, "Sport": "NCAAF", "Bet": "Air Force TT Over", "Bet Type": "Total", "Bet Line": 28.5, "Bet Price": -105.0, "Result": "Win", "Profit": 100, "Running Profit": -461.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 106.0, "Sport": "NCAAF", "Bet": "Air Force TT Over", "Bet Type": "Total", "Bet Line": 28.5, "Bet Price": -106.0, "Result": "Win", "Profit": 100, "Running Profit": -361.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Tunes", "Sportsbook": "Draft Kings", "Bet Amount": 55.0, "Sport": "NFL", "Bet": "Saints", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -416.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 110.0, "Sport": "NFL", "Bet": "Chiefs", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -110.0, "Result": "Win", "Profit": 100, "Running Profit": -316.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 110.0, "Sport": "NFL", "Bet": "Chiefs", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -110.0, "Result": "Win", "Profit": 100, "Running Profit": -216.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 210.0, "Sport": "NFL", "Bet": "Falcons ", "Bet Type": "Side", "Bet Line": 4.5, "Bet Price": -105.0, "Result": "Win", "Profit": 200, "Running Profit": -16.06569563, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 51.0, "Sport": "NCAAF", "Bet": "Western Kentucky ", "Bet Type": "Side", "Bet Line": -7.5, "Bet Price": -102.0, "Result": "Loss", "Profit": -51, "Running Profit": -67.06569563, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "ole miss", "Bet Type": "Side", "Bet Line": 5.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -122.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "texas tech", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -177.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Jax st", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -127.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "UTEP", "Bet Type": "Side", "Bet Line": 4.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -77.06569563, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "ECU", "Bet Type": "Side", "Bet Line": -16.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -132.0656956, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "iowa", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -122.0, "Result": "Win", "Profit": 49.18032787, "Running Profit": -82.88536776, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "unc", "Bet Type": "Side", "Bet Line": 13.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -32.88536776, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "nebraska", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -90.38536776, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "vandy/lsu over", "Bet Type": "Total", "Bet Line": 44.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -40.38536776, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "uconn", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -114.0, "Result": "Win", "Profit": 49.12280702, "Running Profit": 8.737439257, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "texas  ", "Bet Type": "Side", "Bet Line": -12.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -46.26256074, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "georgia southern", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 3.737439257, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "memphis", "Bet Type": "Side", "Bet Line": -20.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -51.26256074, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "oklahoma", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1.262560743, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Hard Rock", "Bet Amount": 28.75, "Sport": "NCAAF", "Bet": "North texas", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -115.0, "Result": "Win", "Profit": 25, "Running Profit": 23.73743926, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 28.75, "Sport": "NCAAF", "Bet": "North texas", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -115.0, "Result": "Win", "Profit": 25, "Running Profit": 48.73743926, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 27.5, "Sport": "NCAAF", "Bet": "syracuse", "Bet Type": "Side", "Bet Line": 10.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -27.5, "Running Profit": 21.23743926, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 30.0, "Sport": "NCAAF", "Bet": "syracuse", "Bet Type": "Side", "Bet Line": 11.5, "Bet Price": -120.0, "Result": "Loss", "Profit": -30, "Running Profit": -8.762560743, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "louisville/miami under", "Bet Type": "Total", "Bet Line": 50.5, "Bet Price": -105.0, "Result": "Win", "Profit": 50, "Running Profit": 41.23743926, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "louisville ", "Bet Type": "Side", "Bet Line": 13.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 91.23743926, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "duke", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -120.0, "Result": "Loss", "Profit": -60, "Running Profit": 31.23743926, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "texas st", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -230, "Running Profit": -198.7625607, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 224.0, "Sport": "NCAAF", "Bet": "ULM", "Bet Type": "Side", "Bet Line": 6.0, "Bet Price": -112.0, "Result": "Loss", "Profit": -224, "Running Profit": -422.7625607, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "duke/gt under", "Bet Type": "Total", "Bet Line": 60.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -372.7625607, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 240.0, "Sport": "NCAAF", "Bet": "Boise TTo36.5", "Bet Type": "Total", "Bet Line": 36.5, "Bet Price": -120.0, "Result": "Win", "Profit": 200, "Running Profit": -172.7625607, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "Tcu", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -130.0, "Result": "Win", "Profit": 46.15384615, "Running Profit": -126.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Ucf", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -76.60871459, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Hard Rock", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Air Force ", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -134.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 235.0, "Sport": "NCAAF", "Bet": "Purdue", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -117.0, "Result": "Loss", "Profit": -235, "Running Profit": -369.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "10/18/2025", "Account": "James", "Bet Description": "", "Source": "Tunes", "Sportsbook": "Prime", "Bet Amount": 53.0, "Sport": "NFL", "Bet": "Browns/dolphins over", "Bet Type": "Total", "Bet Line": 34.5, "Bet Price": -106.0, "Result": "Win", "Profit": 50, "Running Profit": -319.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "77 bets", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 220.0, "Sport": "NFL", "Bet": "seattle", "Bet Type": "Side", "Bet Line": -3.0, "Bet Price": -110.0, "Result": "Win", "Profit": 200, "Running Profit": -119.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": 472.0, "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Michigan", "Bet Type": "Side", "Bet Line": -11.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -176.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": 0.1076396807, "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "Rutgers", "Bet Type": "Side", "Bet Line": 1.5, "Bet Price": -112.0, "Result": "Win", "Profit": 50, "Running Profit": -126.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "vandy/mizzou over", "Bet Type": "Total", "Bet Line": 50.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -181.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "LSU", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -122.0, "Result": "Loss", "Profit": -60, "Running Profit": -241.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Delaware", "Bet Type": "Side", "Bet Line": -8.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -296.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "SMU", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -351.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "oregon/wisc over", "Bet Type": "Total", "Bet Line": 44.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -406.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Prime", "Bet Amount": 55.5, "Sport": "NCAAF", "Bet": "Texas", "Bet Type": "Side", "Bet Line": -6.0, "Bet Price": -111.0, "Result": "Win", "Profit": 50, "Running Profit": -356.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "Cincinnati", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -105.0, "Result": "Win", "Profit": 50, "Running Profit": -306.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "oregon ", "Bet Type": "Side", "Bet Line": -32.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -364.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "memphis", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -314.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "southern miss", "Bet Type": "Side", "Bet Line": -11.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -264.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "ohio", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -319.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "sdst", "Bet Type": "Side", "Bet Line": -1.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -269.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "north texas", "Bet Type": "Side", "Bet Line": -24.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -219.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "south alabama", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -169.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "toledo", "Bet Type": "Side", "Bet Line": 2.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -224.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Steam", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Illinois/wash under ", "Bet Type": "Total", "Bet Line": 56.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -279.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Nc state", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -334.1087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 55.5, "Sport": "NCAAF", "Bet": "bowling green", "Bet Type": "Side", "Bet Line": -8.0, "Bet Price": -111.0, "Result": "Loss", "Profit": -55.5, "Running Profit": -389.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 53.0, "Sport": "NCAAF", "Bet": "houston", "Bet Type": "Side", "Bet Line": 8.5, "Bet Price": -106.0, "Result": "Win", "Profit": 50, "Running Profit": -339.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Steam", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "Texas A&M/LSU Over", "Bet Type": "Total", "Bet Line": 48.5, "Bet Price": -105.0, "Result": "Win", "Profit": 50, "Running Profit": -289.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Steam", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "middle tenn state", "Bet Type": "Side", "Bet Line": 10.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -239.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 120.0, "Sport": "NCAAF", "Bet": "FIU", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -120.0, "Result": "Loss", "Profit": -120, "Running Profit": -359.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 105.0, "Sport": "NCAAF", "Bet": "FIU", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -105.0, "Result": "Loss", "Profit": -105, "Running Profit": -464.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 115.0, "Sport": "NCAAF", "Bet": "Fresno ", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -115, "Running Profit": -579.6087146, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 100.0, "Sport": "NFL", "Bet": "Bills -1/eagles -1.5", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -120.0, "Result": "Win", "Profit": 83.33333333, "Running Profit": -496.2753813, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 150.0, "Sport": "NFL", "Bet": "Bills -1/eagles -1.5", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -135.0, "Result": "Win", "Profit": 111.1111111, "Running Profit": -385.1642701, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "Akron TT U17.5", "Bet Type": "Total", "Bet Line": 17.5, "Bet Price": -112.0, "Result": "Loss", "Profit": -56, "Running Profit": -441.1642701, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Steam", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "lousiville/bc under", "Bet Type": "Total", "Bet Line": 54.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -60, "Running Profit": -501.1642701, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Steam", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "arkst/geo southern under", "Bet Type": "Total", "Bet Line": 62.5, "Bet Price": -115.0, "Result": "Win", "Profit": 47.82608696, "Running Profit": -453.3381832, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "Arkansas", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -116.0, "Result": "Loss", "Profit": -230, "Running Profit": -683.3381832, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 230.0, "Sport": "NFL", "Bet": "Texans", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -115.0, "Result": "Win", "Profit": 200, "Running Profit": -483.3381832, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 52.5, "Sport": "NFL", "Bet": "Vikings TT over 20.5", "Bet Type": "Total", "Bet Line": 20.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -52.5, "Running Profit": -535.8381832, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Steam", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "houston/arizona over", "Bet Type": "Total", "Bet Line": 45.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -590.8381832, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 27.5, "Sport": "NCAAF", "Bet": "Michigan state ", "Bet Type": "Side", "Bet Line": 14.5, "Bet Price": -110.0, "Result": "Win", "Profit": 25, "Running Profit": -565.8381832, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 28.75, "Sport": "NCAAF", "Bet": "Michigan state ", "Bet Type": "Side", "Bet Line": 15.5, "Bet Price": -115.0, "Result": "Win", "Profit": 25, "Running Profit": -540.8381832, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 15.0, "Sport": "NCAAF", "Bet": "Michigan state ", "Bet Type": "Side", "Bet Line": 16.5, "Bet Price": -120.0, "Result": "Win", "Profit": 12.5, "Running Profit": -528.3381832, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 150.0, "Sport": "NCAAF", "Bet": "Michigan state ", "Bet Type": "Side", "Bet Line": 14.5, "Bet Price": -122.0, "Result": "Win", "Profit": 122.9508197, "Running Profit": -405.3873635, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 172.5, "Sport": "NFL", "Bet": "Pittsburgh", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -172.5, "Running Profit": -577.8873635, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 57.5, "Sport": "NFL", "Bet": "Pittsburgh ", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -635.3873635, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "So miss under ", "Bet Type": "Total", "Bet Line": 50.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -692.8873635, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Hard Rock", "Bet Amount": 43.13, "Sport": "NCAAF", "Bet": "Miami ", "Bet Type": "Side", "Bet Line": -1.5, "Bet Price": -115.0, "Result": "Win", "Profit": 37.50434783, "Running Profit": -655.3830157, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Hard Rock", "Bet Amount": 25.0, "Sport": "NCAAF", "Bet": "Miami ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -125.0, "Result": "Win", "Profit": 20, "Running Profit": -635.3830157, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Fan Duel", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Vanderbilt", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": 109.0, "Result": "Win", "Profit": 21.8, "Running Profit": -613.5830157, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Hard Rock", "Bet Amount": 45.0, "Sport": "NCAAF", "Bet": "Vanderbilt ", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -120.0, "Result": "Win", "Profit": 37.5, "Running Profit": -576.0830157, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Berryhorse", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Troy under ", "Bet Type": "Total", "Bet Line": 48.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -633.5830157, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Steam", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "utah", "Bet Type": "Side", "Bet Line": -12.5, "Bet Price": -113.0, "Result": "Win", "Profit": 48.67256637, "Running Profit": -584.9104493, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 122.0, "Sport": "NCAAF", "Bet": "Nc state TT O23.5", "Bet Type": "Total", "Bet Line": 23.5, "Bet Price": -122.0, "Result": "Win", "Profit": 100, "Running Profit": -484.9104493, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 115.0, "Sport": "NCAAF", "Bet": "Nc state TT O23.5", "Bet Type": "Total", "Bet Line": 23.5, "Bet Price": -115.0, "Result": "Win", "Profit": 100, "Running Profit": -384.9104493, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 165.0, "Sport": "NCAAF", "Bet": "Minnesota ", "Bet Type": "Side", "Bet Line": 9.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -165, "Running Profit": -549.9104493, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Minnesota ", "Bet Type": "Side", "Bet Line": 9.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -604.9104493, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 210.0, "Sport": "NCAAF", "Bet": "North Dakota state ", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -125.0, "Result": "Win", "Profit": 168, "Running Profit": -436.9104493, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 10.0, "Sport": "NCAAF", "Bet": "North Dakota state ", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -105.0, "Result": "Win", "Profit": 9.523809524, "Running Profit": -427.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 125.0, "Sport": "NCAAF", "Bet": "Hampton", "Bet Type": "Side", "Bet Line": 28.5, "Bet Price": -125.0, "Result": "Win", "Profit": 100, "Running Profit": -327.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "11/2/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 250.0, "Sport": "NCAAF", "Bet": "UL Monroe TT U17.5", "Bet Type": "Total", "Bet Line": 17.5, "Bet Price": -125.0, "Result": "Loss", "Profit": -250, "Running Profit": -577.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": 6661, "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Tulane/UTSA Over", "Bet Type": "Total", "Bet Line": 53.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -527.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": 407, "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "UTEP", "Bet Type": "Side", "Bet Line": 14.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -477.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": 0.06110193665, "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "SMU", "Bet Type": "Side", "Bet Line": 10.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -427.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "SMU/Miami Over", "Bet Type": "Total", "Bet Line": 51.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -482.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Marshall ", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -539.8866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Ohio st/psu over ", "Bet Type": "Total", "Bet Line": 44.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -489.8866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "Texas", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -105.0, "Result": "Win", "Profit": 50, "Running Profit": -439.8866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "memphis", "Bet Type": "Side", "Bet Line": -13.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -389.8866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "Syracuse", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -120.0, "Result": "Loss", "Profit": -60, "Running Profit": -449.8866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "Colorado", "Bet Type": "Side", "Bet Line": 5.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -52.5, "Running Profit": -502.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "minnesota/mich st over", "Bet Type": "Total", "Bet Line": 44.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -557.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "michigan ", "Bet Type": "Side", "Bet Line": -19.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -612.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "troy", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -667.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "virginia", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -617.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "UCF", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -672.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Louisiana Tech", "Bet Type": "Side", "Bet Line": -16.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -622.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "bowling green", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -677.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "illinois/rutgers over", "Bet Type": "Total", "Bet Line": 61.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -732.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "utep kennesaw over", "Bet Type": "Total", "Bet Line": 50.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -682.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "marshall/coastal under", "Bet Type": "Total", "Bet Line": 55.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -737.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Draft Kings", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "clemson/duke over", "Bet Type": "Total", "Bet Line": 53.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -687.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Kansas/okst over ", "Bet Type": "Total", "Bet Line": 55.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -637.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Sjst/Hawaii over ", "Bet Type": "Total", "Bet Line": 55.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -587.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "florida state/wake under", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -537.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 175.0, "Sport": "NCAAF", "Bet": "USC Nebraska over ", "Bet Type": "Total", "Bet Line": 58.5, "Bet Price": -112.0, "Result": "Loss", "Profit": -175, "Running Profit": -712.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 64.0, "Sport": "NCAAF", "Bet": "USC Nebraska over ", "Bet Type": "Total", "Bet Line": 58.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -64, "Running Profit": -776.3866398, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "Georgia ", "Bet Type": "Side", "Bet Line": -7.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -230, "Running Profit": -1006.38664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 30.0, "Sport": "NCAAF", "Bet": "Texas st", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -30, "Running Profit": -1036.38664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Prime", "Bet Amount": 59.0, "Sport": "NCAAF", "Bet": "cal/virginia over", "Bet Type": "Total", "Bet Line": 53.5, "Bet Price": -118.0, "Result": "Loss", "Profit": -59, "Running Profit": -1095.38664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 53.0, "Sport": "NCAAF", "Bet": "vanderbilt/texas under", "Bet Type": "Total", "Bet Line": 45.5, "Bet Price": -106.0, "Result": "Loss", "Profit": -53, "Running Profit": -1148.38664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Prime", "Bet Amount": 53.5, "Sport": "NCAAF", "Bet": "wake forest", "Bet Type": "Side", "Bet Line": 10.0, "Bet Price": -107.0, "Result": "Loss", "Profit": -53.5, "Running Profit": -1201.88664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "Prime", "Bet Amount": 55.5, "Sport": "NCAAF", "Bet": "virginia tech", "Bet Type": "Side", "Bet Line": 11.0, "Bet Price": -111.0, "Result": "Loss", "Profit": -55.5, "Running Profit": -1257.38664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Bud", "Sportsbook": "MGM", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "kansas st/tech under", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -1314.88664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 135.0, "Sport": "NFL", "Bet": "Bills/lions", "Bet Type": "Parlay", "Bet Line": "8/-2.5", "Bet Price": -135.0, "Result": "Loss", "Profit": -135, "Running Profit": -1449.88664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 120.0, "Sport": "NFL", "Bet": "Bills/lions", "Bet Type": "Parlay", "Bet Line": "8/-2.5", "Bet Price": -130.0, "Result": "Loss", "Profit": -120, "Running Profit": -1569.88664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 120.0, "Sport": "NCAAF", "Bet": "Tennessee", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -120.0, "Result": "Loss", "Profit": -120, "Running Profit": -1689.88664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 28.75, "Sport": "NCAAF", "Bet": "Tennessee", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -28.75, "Running Profit": -1718.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 60.5, "Sport": "NCAAF", "Bet": "Tennessee", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -121.0, "Result": "Loss", "Profit": -60.5, "Running Profit": -1779.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 35.0, "Sport": "NCAAF", "Bet": "Tennessee", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -140.0, "Result": "Loss", "Profit": -35, "Running Profit": -1814.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Tennessee", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -109.0, "Result": "Loss", "Profit": -20, "Running Profit": -1834.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 44.0, "Sport": "NCAAF", "Bet": "Bryant", "Bet Type": "Side", "Bet Line": 15.5, "Bet Price": -113.0, "Result": "Loss", "Profit": -44, "Running Profit": -1878.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 11.0, "Sport": "NCAAF", "Bet": "Bryant", "Bet Type": "Side", "Bet Line": 16.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -11, "Running Profit": -1889.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Delaware", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -1946.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 172.5, "Sport": "NCAAF", "Bet": "Delaware", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -172.5, "Running Profit": -2119.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 224.0, "Sport": "NCAAF", "Bet": "New Mexico", "Bet Type": "Side", "Bet Line": 4.5, "Bet Price": -112.0, "Result": "Win", "Profit": 200, "Running Profit": -1919.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 105.0, "Sport": "NFL", "Bet": "Atlanta", "Bet Type": "Side", "Bet Line": 5.0, "Bet Price": -105.0, "Result": "Win", "Profit": 100, "Running Profit": -1819.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 120.0, "Sport": "NFL", "Bet": "Pittsburgh ", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -120.0, "Result": "Win", "Profit": 100, "Running Profit": -1719.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "118 bets", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "iowa/oregon over", "Bet Type": "Total", "Bet Line": 42.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1774.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": 6661, "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "ball st/kent st over", "Bet Type": "Total", "Bet Line": 46.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1829.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": 407, "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "texas A&M", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1779.13664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": 0.06110193665, "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "indiana", "Bet Type": "Side", "Bet Line": -10.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -52.5, "Running Profit": -1831.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "nebraska", "Bet Type": "Side", "Bet Line": 1.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1781.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "connecticut", "Bet Type": "Side", "Bet Line": 12.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1731.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "virginia", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1786.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "SMU", "Bet Type": "Side", "Bet Line": -11.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1736.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "washington ", "Bet Type": "Side", "Bet Line": -10.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1791.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "miami-oh", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1846.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "sdst", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1901.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Iowa st/Tcu over ", "Bet Type": "Total", "Bet Line": 56.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1956.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Oregon", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -2011.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "la tech", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -2066.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "southern miss", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -2016.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "southern miss/ark st under", "Bet Type": "Total", "Bet Line": 59.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1966.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "oregon st/shst over", "Bet Type": "Total", "Bet Line": 51.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -2021.63664, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 165.0, "Sport": "NCAAF", "Bet": "Texas A&M", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -115.0, "Result": "Win", "Profit": 143.4782609, "Running Profit": -1878.158379, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Texas A&M", "Bet Type": "Side", "Bet Line": -6.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1828.158379, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 244.0, "Sport": "NCAAF", "Bet": "Eastern Michigan", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -122.0, "Result": "Win", "Profit": 200, "Running Profit": -1628.158379, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 110.0, "Sport": "NFL", "Bet": "Tampa bay", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -110, "Running Profit": -1738.158379, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 110.0, "Sport": "NFL", "Bet": "Tampa bay", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -110, "Running Profit": -1848.158379, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 107.0, "Sport": "NCAAF", "Bet": "james madison over", "Bet Type": "Total", "Bet Line": 54.0, "Bet Price": -107.0, "Result": "Win", "Profit": 100, "Running Profit": -1748.158379, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 105.0, "Sport": "NCAAF", "Bet": "james madison over", "Bet Type": "Total", "Bet Line": 54.5, "Bet Price": -105.0, "Result": "Win", "Profit": 100, "Running Profit": -1648.158379, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Ucf", "Bet Type": "Side", "Bet Line": 1.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -1705.658379, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 240.0, "Sport": "NCAAF", "Bet": "navy TT O13.5", "Bet Type": "Total", "Bet Line": 13.5, "Bet Price": -120.0, "Result": "Loss", "Profit": -240, "Running Profit": -1945.658379, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 50.0, "Sport": "NCAAF", "Bet": "texas A&M", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -106.0, "Result": "Win", "Profit": 47.16981132, "Running Profit": -1898.488568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open ", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Northern Illinois ", "Bet Type": "Side", "Bet Line": -11.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -1848.488568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open ", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "utah", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -1798.488568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open ", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "Troy", "Bet Type": "Side", "Bet Line": 10.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -52.5, "Running Profit": -1850.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open ", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "marshall", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -1800.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open ", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "washington ", "Bet Type": "Side", "Bet Line": -13.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1750.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open ", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "oregon ", "Bet Type": "Side", "Bet Line": -20.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1700.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "North Carolina ", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -1758.488568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "oregon state", "Bet Type": "Side", "Bet Line": 1.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -1815.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "oregon/minnesota over", "Bet Type": "Total", "Bet Line": 44.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1765.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Coastal over ", "Bet Type": "Total", "Bet Line": 58.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1715.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "Oklahoma ", "Bet Type": "Side", "Bet Line": 7.0, "Bet Price": -115.0, "Result": "Win", "Profit": 200, "Running Profit": -1515.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "Georgia southern", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Win", "Profit": 200, "Running Profit": -1315.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 72.0, "Sport": "NFL", "Bet": "Minnesota", "Bet Type": "Side", "Bet Line": -3.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -72, "Running Profit": -1387.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 109.0, "Sport": "NFL", "Bet": "Minnesota", "Bet Type": "Side", "Bet Line": -3.0, "Bet Price": -109.0, "Result": "Loss", "Profit": -109, "Running Profit": -1496.988568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 36.75, "Sport": "NFL", "Bet": "Minnesota", "Bet Type": "Side", "Bet Line": -3.0, "Bet Price": -105.0, "Result": "Loss", "Profit": -36.75, "Running Profit": -1533.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Purdue Washington under ", "Bet Type": "Total", "Bet Line": 53.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1588.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Kst/okst under ", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1538.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 220.0, "Sport": "NCAAF", "Bet": "Duke ", "Bet Type": "Side", "Bet Line": -4.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -220, "Running Profit": -1758.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 226.0, "Sport": "NFL", "Bet": "Jaguars ", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -113.0, "Result": "Win", "Profit": 200, "Running Profit": -1558.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Tennessee ", "Bet Type": "Side", "Bet Line": -38.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -1616.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Bud", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "New Mexico ", "Bet Type": "Side", "Bet Line": -14.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -52.5, "Running Profit": -1668.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "kentucky ", "Bet Type": "Side", "Bet Line": -21.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1618.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 220.0, "Sport": "NCAAF", "Bet": "ND/Pitt Over", "Bet Type": "Total", "Bet Line": 54.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -220, "Running Profit": -1838.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 216.0, "Sport": "NCAAF", "Bet": "Jax St", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -108.0, "Result": "Win", "Profit": 200, "Running Profit": -1638.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 216.0, "Sport": "NCAAF", "Bet": "USC/Iowa Under", "Bet Type": "Total", "Bet Line": 48.5, "Bet Price": -108.0, "Result": "Win", "Profit": 200, "Running Profit": -1438.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Ohio", "Bet Type": "Side", "Bet Line": -29.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -1496.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Stanford", "Bet Type": "Side", "Bet Line": 4.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1446.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "texas", "Bet Type": "Side", "Bet Line": -10.5, "Bet Price": -105.0, "Result": "Win", "Profit": 50, "Running Profit": -1396.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "tennessee", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -112.0, "Result": "Win", "Profit": 50, "Running Profit": -1346.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "tcu", "Bet Type": "Side", "Bet Line": 2.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -1296.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 61.0, "Sport": "NCAAF", "Bet": "pittsburgh", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -122.0, "Result": "Win", "Profit": 50, "Running Profit": -1246.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "army", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1301.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "UCF", "Bet Type": "Side", "Bet Line": -15.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1356.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.0, "Sport": "NCAAF", "Bet": "iowa", "Bet Type": "Side", "Bet Line": -15.5, "Bet Price": -114.0, "Result": "Loss", "Profit": -57, "Running Profit": -1413.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "ohio state/rutgers over", "Bet Type": "Total", "Bet Line": 55.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1468.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "FAU/uconn under", "Bet Type": "Total", "Bet Line": 67.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1523.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "okst/ucf over", "Bet Type": "Total", "Bet Line": 47.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1578.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "toledo", "Bet Type": "Side", "Bet Line": -24.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1528.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "tulane/temple over", "Bet Type": "Total", "Bet Line": 54.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -1585.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "san diego st", "Bet Type": "Side", "Bet Line": -10.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -1535.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "nevada", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -1485.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Miami ", "Bet Type": "Side", "Bet Line": -16.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -1435.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Mardhall/app over ", "Bet Type": "Total", "Bet Line": 53.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -1490.738568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Ga southern ", "Bet Type": "Side", "Bet Line": 12.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -1548.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 115.0, "Sport": "NCAAF", "Bet": "Hawaii ", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -115, "Running Profit": -1663.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 65.0, "Sport": "NCAAF", "Bet": "Hawaii ", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -130.0, "Result": "Loss", "Profit": -65, "Running Profit": -1728.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 57.0, "Sport": "NCAAF", "Bet": "Hawaii ", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -114.0, "Result": "Loss", "Profit": -57, "Running Profit": -1785.238568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "oregon", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": 101.0, "Result": "Win", "Profit": 20.2, "Running Profit": -1765.038568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "north texas/rice over", "Bet Type": "Total", "Bet Line": 55.5, "Bet Price": -115.0, "Result": "Win", "Profit": 200, "Running Profit": -1565.038568, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 145.0, "Sport": "NCAAF", "Bet": "SMU", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Win", "Profit": 126.0869565, "Running Profit": -1438.951611, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 45.0, "Sport": "NCAAF", "Bet": "SMU", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -120.0, "Result": "Win", "Profit": 37.5, "Running Profit": -1401.451611, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 48.47, "Sport": "NCAAF", "Bet": "SMU", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -131.0, "Result": "Win", "Profit": 37, "Running Profit": -1364.451611, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 45.0, "Sport": "NCAAF", "Bet": "Ohio state TT U42.5", "Bet Type": "Total", "Bet Line": 42.5, "Bet Price": -120.0, "Result": "Win", "Profit": 37.5, "Running Profit": -1326.951611, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 204.8, "Sport": "NCAAF", "Bet": "Ohio state TT U42.5", "Bet Type": "Total", "Bet Line": 42.5, "Bet Price": -128.0, "Result": "Win", "Profit": 160, "Running Profit": -1166.951611, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 235.0, "Sport": "NCAAF", "Bet": "Oregon TT O34.5", "Bet Type": "Total", "Bet Line": 34.5, "Bet Price": -125.0, "Result": "Win", "Profit": 188, "Running Profit": -978.9516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NCAAF", "Bet": "Oregon TT O34.5", "Bet Type": "Total", "Bet Line": 34.5, "Bet Price": 118.0, "Result": "Win", "Profit": 11.8, "Running Profit": -967.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 130.0, "Sport": "NFL", "Bet": "Steelers+9/cards+8.5", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -130.0, "Result": "Win", "Profit": 100, "Running Profit": -867.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 125.0, "Sport": "NFL", "Bet": "Steelers+9/cards+8.5", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -125.0, "Result": "Win", "Profit": 100, "Running Profit": -767.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Virginia", "Bet Type": "Side", "Bet Line": -8.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -717.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "syracuse", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -112.0, "Result": "Loss", "Profit": -56, "Running Profit": -773.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Missouri", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -723.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "alabama", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -673.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "penn st", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -728.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 61.0, "Sport": "NCAAF", "Bet": "texas", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -122.0, "Result": "Win", "Profit": 50, "Running Profit": -678.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "Fresno State ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -120.0, "Result": "Win", "Profit": 50, "Running Profit": -628.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "NC State", "Bet Type": "Side", "Bet Line": -7.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -578.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 54.0, "Sport": "NCAAF", "Bet": "Cincinnati", "Bet Type": "Side", "Bet Line": 4.5, "Bet Price": -108.0, "Result": "Loss", "Profit": -54, "Running Profit": -632.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Prime", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "East Carolina", "Bet Type": "Side", "Bet Line": -6.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -582.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "Troy", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -112.0, "Result": "Win", "Profit": 50, "Running Profit": -532.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "USC", "Bet Type": "Side", "Bet Line": -18.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -482.1516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Prime", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "iowa state", "Bet Type": "Side", "Bet Line": -14.0, "Bet Price": -105.0, "Result": "Loss", "Profit": -52.5, "Running Profit": -534.6516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Maryland", "Bet Type": "Side", "Bet Line": 4.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -589.6516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "Florida/FSU Under", "Bet Type": "Total", "Bet Line": 52.5, "Bet Price": -120.0, "Result": "Loss", "Profit": -60, "Running Profit": -649.6516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "South Florida ", "Bet Type": "Side", "Bet Line": -25.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -599.6516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Ohio state ", "Bet Type": "Side", "Bet Line": -7.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -549.6516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Oregon st/wash st under ", "Bet Type": "Total", "Bet Line": 43.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -499.6516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "miss/miss st under", "Bet Type": "Total", "Bet Line": 63.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -449.6516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 56.0, "Sport": "NCAAF", "Bet": "northern illinois", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -56, "Running Profit": -505.6516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "air force/colo st under", "Bet Type": "Total", "Bet Line": 49.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -560.6516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "ohio/buff under", "Bet Type": "Total", "Bet Line": 47.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -615.6516111, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 63.3, "Sport": "NCAAF", "Bet": "OKST/IOwa st under", "Bet Type": "Total", "Bet Line": 48.5, "Bet Price": -110.0, "Result": "Win", "Profit": 57.54545455, "Running Profit": -558.1061565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 175.0, "Sport": "NCAAF", "Bet": "OKST/IOwa st under", "Bet Type": "Total", "Bet Line": 48.5, "Bet Price": -112.0, "Result": "Win", "Profit": 156.25, "Running Profit": -401.8561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "Georgia", "Bet Type": "Side", "Bet Line": -13.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -230, "Running Profit": -631.8561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 216.0, "Sport": "NCAAF", "Bet": "Tulsa", "Bet Type": "Side", "Bet Line": -8.5, "Bet Price": -108.0, "Result": "Loss", "Profit": -216, "Running Profit": -847.8561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 25.0, "Sport": "NCAAF", "Bet": "Ohio state ", "Bet Type": "Side", "Bet Line": -9.5, "Bet Price": 134.0, "Result": "Win", "Profit": 33.5, "Running Profit": -814.3561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 200.0, "Sport": "NCAAF", "Bet": "Stanford TT o7.5", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": 100.0, "Result": "Win", "Profit": 200, "Running Profit": -614.3561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 121.0, "Sport": "NFL", "Bet": "Commanders", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -121.0, "Result": "Win", "Profit": 100, "Running Profit": -514.3561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 119.0, "Sport": "NFL", "Bet": "Commanders", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -119.0, "Result": "Win", "Profit": 100, "Running Profit": -414.3561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "miami", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -469.3561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 150.0, "Sport": "NCAAF", "Bet": "Georgia sec", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -150.0, "Result": "Win", "Profit": 100, "Running Profit": -369.3561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 150.0, "Sport": "NCAAF", "Bet": "Georgia sec ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -150.0, "Result": "Win", "Profit": 100, "Running Profit": -269.3561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 60.0, "Sport": "NCAAF", "Bet": "kennesaw st", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -120.0, "Result": "Win", "Profit": 50, "Running Profit": -219.3561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NCAAF", "Bet": "South Dakota state ", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -120.0, "Result": "Loss", "Profit": -10, "Running Profit": -229.3561565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 133.51, "Sport": "NCAAF", "Bet": "South Dakota state ", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -115.0, "Result": "Loss", "Profit": -133.51, "Running Profit": -362.8661565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 90.75, "Sport": "NCAAF", "Bet": "South Dakota state ", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -121.0, "Result": "Loss", "Profit": -90.75, "Running Profit": -453.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 240.0, "Sport": "NFL", "Bet": "Chargers8.5/rams-2.5", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -120.0, "Result": "Win", "Profit": 200, "Running Profit": -253.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Ohio State ", "Bet Type": "Side", "Bet Line": -4.0, "Bet Price": 139.0, "Result": "Loss", "Profit": -20, "Running Profit": -273.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Ohio State ", "Bet Type": "Side", "Bet Line": -4.0, "Bet Price": 120.0, "Result": "Loss", "Profit": -20, "Running Profit": -293.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Ohio State ", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": 109.0, "Result": "Loss", "Profit": -20, "Running Profit": -313.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Hard Rock", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Ohio State ", "Bet Type": "Side", "Bet Line": -3.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -371.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 80.0, "Sport": "NCAAF", "Bet": "Ohio State ", "Bet Type": "Side", "Bet Line": -4.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -80, "Running Profit": -451.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 396.0, "Sport": "NFL", "Bet": "Kansas city", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -198.0, "Result": "Loss", "Profit": -396, "Running Profit": -847.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "South Florida", "Bet Type": "Side", "Bet Line": -7.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -902.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 130.0, "Sport": "NCAAF", "Bet": "Alabama ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -125.0, "Result": "Win", "Profit": 104, "Running Profit": -798.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "miami", "Bet Type": "Side", "Bet Line": 5.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -748.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "bama/okla over", "Bet Type": "Total", "Bet Line": 40.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -698.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "oregon", "Bet Type": "Side", "Bet Line": -19.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -753.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Caesers", "Bet Amount": 105.0, "Sport": "NCAAF", "Bet": "ohio state make title", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 107.0, "Result": "Loss", "Profit": -105, "Running Profit": -858.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 165.0, "Sport": "NCAAF", "Bet": "BigTen win title", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -165.0, "Result": "", "Profit": -165, "Running Profit": -1023.116157, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Caesers", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Iowa", "Bet Type": "Side", "Bet Line": 5.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -973.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "BYU", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -923.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 56.5, "Sport": "NCAAF", "Bet": "Ole miss", "Bet Type": "Side", "Bet Line": -16.5, "Bet Price": -113.0, "Result": "Win", "Profit": 50, "Running Profit": -873.1161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 52.5, "Sport": "NCAAF", "Bet": "kennesaw st", "Bet Type": "Side", "Bet Line": 4.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -52.5, "Running Profit": -925.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "utah st/wash st under", "Bet Type": "Total", "Bet Line": 54.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -980.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "miami/fresno under", "Bet Type": "Total", "Bet Line": 43.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -930.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Toledo/louisville under", "Bet Type": "Total", "Bet Line": 46.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -985.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Open", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Washington ", "Bet Type": "Side", "Bet Line": -8.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -935.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Virginia ", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -885.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "tennessee/illinois under", "Bet Type": "Total", "Bet Line": 61.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -835.6161565, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 75.0, "Sport": "NCAAF", "Bet": "Texas ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -185.0, "Result": "Win", "Profit": 40.54054054, "Running Profit": -795.075616, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 134.75, "Sport": "NCAAF", "Bet": "Duke", "Bet Type": "Side", "Bet Line": -1.5, "Bet Price": -115.0, "Result": "Win", "Profit": 117.173913, "Running Profit": -677.901703, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 100.0, "Sport": "NCAAF", "Bet": "Duke", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -120.0, "Result": "Win", "Profit": 83.33333333, "Running Profit": -594.5683696, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 260.0, "Sport": "NFL", "Bet": "Bears-1 / broncos +7.5", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -130.0, "Result": "Win", "Profit": 200, "Running Profit": -394.5683696, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 100.0, "Sport": "NFL", "Bet": "Steelers", "Bet Type": "Side", "Bet Line": -3.0, "Bet Price": -112.0, "Result": "Win", "Profit": 89.28571429, "Running Profit": -305.2826553, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Steelers", "Bet Type": "Side", "Bet Line": -4.5, "Bet Price": 134.0, "Result": "Win", "Profit": 26.8, "Running Profit": -278.4826553, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 57.5, "Sport": "NCAAF", "Bet": "Tcu", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -228.4826553, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 220.0, "Sport": "NFL", "Bet": "Seattle", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -110.0, "Result": "Win", "Profit": 200, "Running Profit": -28.48265533, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Oregon TT over 32.5", "Bet Type": "Total", "Bet Line": 32.5, "Bet Price": 108.0, "Result": "Win", "Profit": 21.6, "Running Profit": -6.882655333, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 90.0, "Sport": "NCAAF", "Bet": "Oregon TT over 33.5", "Bet Type": "Total", "Bet Line": 33.5, "Bet Price": -115.0, "Result": "Win", "Profit": 78.26086957, "Running Profit": 71.37821423, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 120.0, "Sport": "NCAAF", "Bet": "Oregon TT over 33.5", "Bet Type": "Total", "Bet Line": 33.5, "Bet Price": -120.0, "Result": "Win", "Profit": 100, "Running Profit": 171.3782142, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Oklahoma ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 113.0, "Result": "Loss", "Profit": -20, "Running Profit": 151.3782142, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Caesers", "Bet Amount": 115.0, "Sport": "NCAAF", "Bet": "Indiana ", "Bet Type": "Side", "Bet Line": -6.0, "Bet Price": -115.0, "Result": "Win", "Profit": 100, "Running Profit": 251.3782142, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 97.5, "Sport": "NFL", "Bet": "Eagles 0/ packers 7.5", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -130.0, "Result": "Win", "Profit": 75, "Running Profit": 326.3782142, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 112.0, "Sport": "NCAAF", "Bet": "Ohio state ", "Bet Type": "Side", "Bet Line": -8.5, "Bet Price": -112.0, "Result": "Loss", "Profit": -112, "Running Profit": 214.3782142, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NCAAF", "Bet": "Oregon", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 264.3782142, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 55.5, "Sport": "NCAAF", "Bet": "Ole miss", "Bet Type": "Side", "Bet Line": 7.0, "Bet Price": -111.0, "Result": "Win", "Profit": 50, "Running Profit": 314.3782142, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 130.0, "Sport": "NCAAF", "Bet": "Chargers 7.5 / lions -1", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -130.0, "Result": "Loss", "Profit": -130, "Running Profit": 184.3782142, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Fan Duel", "Bet Amount": 122.0, "Sport": "NCAAF", "Bet": "Georgia", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -122.0, "Result": "Loss", "Profit": -122, "Running Profit": 62.37821423, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 115.0, "Sport": "NCAAF", "Bet": "Georgia", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -115, "Running Profit": -52.62178577, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Prime", "Bet Amount": 111.0, "Sport": "NCAAF", "Bet": "Louisville ", "Bet Type": "Side", "Bet Line": -6.5, "Bet Price": -111.0, "Result": "Loss", "Profit": -111, "Running Profit": -163.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Caesers", "Bet Amount": 21.0, "Sport": "NBA", "Bet": "Cavs under 242", "Bet Type": "Total", "Bet Line": 242.0, "Bet Price": -105.0, "Result": "Loss", "Profit": -21, "Running Profit": -184.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NBA", "Bet": "Sgp", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 423.0, "Result": "Loss", "Profit": -20, "Running Profit": -204.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Sgp", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 410.0, "Result": "Loss", "Profit": -20, "Running Profit": -224.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 54.5, "Sport": "NCAAF", "Bet": "Pitt/ecu under ", "Bet Type": "Total", "Bet Line": 53.0, "Bet Price": -109.0, "Result": "Win", "Profit": 50, "Running Profit": -174.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Caesers", "Bet Amount": 250.0, "Sport": "NFL", "Bet": "Houston7.5/rams-2", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -125.0, "Result": "Loss", "Profit": -250, "Running Profit": -424.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 190.0, "Sport": "NFL", "Bet": "san fran", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -190.0, "Result": "Win", "Profit": 100, "Running Profit": -324.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 60.0, "Sport": "NFL", "Bet": "denver", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -120.0, "Result": "Win", "Profit": 50, "Running Profit": -274.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NFL", "Bet": "minnesota", "Bet Type": "Side", "Bet Line": -5.5, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": -224.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NFL", "Bet": "Jets", "Bet Type": "Side", "Bet Line": 11.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -57.5, "Running Profit": -282.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 113.0, "Sport": "NFL", "Bet": "Falcons", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -113.0, "Result": "Win", "Profit": 100, "Running Profit": -182.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 57.5, "Sport": "NFL", "Bet": "Commanders", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -115.0, "Result": "Win", "Profit": 50, "Running Profit": -132.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 55.0, "Sport": "NFL", "Bet": "Commanders under ", "Bet Type": "Total", "Bet Line": 40.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -187.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NCAAF", "Bet": "Miami 1H TT U7.5", "Bet Type": "Total", "Bet Line": 7.5, "Bet Price": -121.0, "Result": "Loss", "Profit": -10, "Running Profit": -197.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 230.0, "Sport": "NCAAF", "Bet": "Oregon TT O26.5", "Bet Type": "Total", "Bet Line": 26.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -230, "Running Profit": -427.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Bonus bet", "Sportsbook": "Draft Kings", "Bet Amount": 125.0, "Sport": "NFL", "Bet": "Packers", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 410.0, "Result": "Loss", "Profit": 0.0, "Running Profit": -427.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Hedge ", "Sportsbook": "Prime", "Bet Amount": 414.0, "Sport": "NFL", "Bet": "Vikings ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -414.0, "Result": "Win", "Profit": 100, "Running Profit": -327.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 110.0, "Sport": "NFL", "Bet": "Steelers", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -110.0, "Result": "Win", "Profit": 100, "Running Profit": -227.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 50.5, "Sport": "NFL", "Bet": "Bills ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -101.0, "Result": "Win", "Profit": 50, "Running Profit": -177.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 115.0, "Sport": "NFL", "Bet": "Texans", "Bet Type": "Side", "Bet Line": -2.5, "Bet Price": -115.0, "Result": "Win", "Profit": 100, "Running Profit": -77.12178577, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Texans win AFC", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 550.0, "Result": "Loss", "Profit": -20, "Running Profit": -97.12178577, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 80.0, "Sport": "NFL", "Bet": "Rams/Eagles", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -160.0, "Result": "Loss", "Profit": -80, "Running Profit": -177.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Caesers", "Bet Amount": 80.0, "Sport": "NFL", "Bet": "Rams/Eagles", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -160.0, "Result": "Loss", "Profit": -80, "Running Profit": -257.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 23.0, "Sport": "NFL", "Bet": "Corum over 43.5 rush yds", "Bet Type": "Total", "Bet Line": 43.5, "Bet Price": -115.0, "Result": "Win", "Profit": 20, "Running Profit": -237.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 23.0, "Sport": "NFL", "Bet": "Coker over 35.5 rec yds", "Bet Type": "Total", "Bet Line": 35.5, "Bet Price": -115.0, "Result": "Win", "Profit": 20, "Running Profit": -217.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NFL", "Bet": "Dowdell o14.5 red yds ", "Bet Type": "Total", "Bet Line": 14.5, "Bet Price": 134.0, "Result": "Loss", "Profit": -10, "Running Profit": -227.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Corum/coker/dowdell", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 507.0, "Result": "Loss", "Profit": -20, "Running Profit": -247.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 60.0, "Sport": "NFL", "Bet": "Texans/rams/eagles", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -120.0, "Result": "Loss", "Profit": -60, "Running Profit": -307.1217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 24.2, "Sport": "NFL", "Bet": "Packers", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": -121.0, "Result": "Loss", "Profit": -24.2, "Running Profit": -331.3217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 22.0, "Sport": "NFL", "Bet": "Reed O35.5 Rec Yds", "Bet Type": "Total", "Bet Line": 35.5, "Bet Price": -110.0, "Result": "Win", "Profit": 20, "Running Profit": -311.3217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 10.0, "Sport": "NFL", "Bet": "Reed TD", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 245.0, "Result": "Win", "Profit": 24.5, "Running Profit": -286.8217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 5.0, "Sport": "NFL", "Bet": "Reed 1st Td", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 1300.0, "Result": "Loss", "Profit": -5, "Running Profit": -291.8217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Packers", "Bet Type": "", "Bet Line": -2.5, "Bet Price": 130.0, "Result": "Loss", "Profit": -20, "Running Profit": -311.8217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Allen over 21.5 completions ", "Bet Type": "", "Bet Line": 21.5, "Bet Price": 101.0, "Result": "Win", "Profit": 20.2, "Running Profit": -291.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 22.0, "Sport": "NFL", "Bet": "Cook under 79.5 rush yds", "Bet Type": "", "Bet Line": 79.5, "Bet Price": -110.0, "Result": "Win", "Profit": 20, "Running Profit": -271.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 22.8, "Sport": "NFL", "Bet": "Strange under 35.5 rec yds", "Bet Type": "", "Bet Line": 35.5, "Bet Price": -114.0, "Result": "Win", "Profit": 20, "Running Profit": -251.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 25.0, "Sport": "NFL", "Bet": "Kincaid over 40.5 rec yds", "Bet Type": "", "Bet Line": 40.5, "Bet Price": -125.0, "Result": "Loss", "Profit": -25, "Running Profit": -276.6217858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 16.26, "Sport": "NFL", "Bet": "Ettiene o2.5 red", "Bet Type": "", "Bet Line": 2.5, "Bet Price": 123.0, "Result": "Win", "Profit": 19.9998, "Running Profit": -256.6219858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NFL", "Bet": "", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 1412.0, "Result": "Loss", "Profit": -10, "Running Profit": -266.6219858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "", "Bet Amount": 10.0, "Sport": "", "Bet": "Kincaid td", "Bet Type": "", "Bet Line": 0.0, "Bet Price": 326.0, "Result": "Win", "Profit": 32.6, "Running Profit": -234.0219858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "", "Bet Amount": 21.0, "Sport": "", "Bet": "Bills/jags under ", "Bet Type": "Total", "Bet Line": 51.5, "Bet Price": -105.0, "Result": "Win", "Profit": 20, "Running Profit": -214.0219858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 52.5, "Sport": "NFL", "Bet": "Chargers", "Bet Type": "Side", "Bet Line": 3.5, "Bet Price": -105.0, "Result": "Loss", "Profit": -52.5, "Running Profit": -266.5219858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 23.4, "Sport": "NFL", "Bet": "Rodgers U205.5 ", "Bet Type": "Total", "Bet Line": 205.5, "Bet Price": -117.0, "Result": "Win", "Profit": 20, "Running Profit": -246.5219858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NFL", "Bet": "rodgers/schultz/freirmuth", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 831.0, "Result": "Loss", "Profit": -10, "Running Profit": -256.5219858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NFL", "Bet": "heyward td", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 820.0, "Result": "Loss", "Profit": -10, "Running Profit": -266.5219858, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 23.0, "Sport": "NFL", "Bet": "rodgers under 31.5 long pass", "Bet Type": "Total", "Bet Line": 31.5, "Bet Price": -114.0, "Result": "Win", "Profit": 20.1754386, "Running Profit": -246.3465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 22.0, "Sport": "NFL", "Bet": "freiermuth over 32 rec yds", "Bet Type": "Total", "Bet Line": "32+", "Bet Price": -110.0, "Result": "Loss", "Profit": -22, "Running Profit": -268.3465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 23.0, "Sport": "NFL", "Bet": "schultz 42+ rec yds", "Bet Type": "Total", "Bet Line": "42+", "Bet Price": -115.0, "Result": "Loss", "Profit": -23, "Running Profit": -291.3465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 55.0, "Sport": "NFL", "Bet": "Texans", "Bet Type": "Side", "Bet Line": 3.0, "Bet Price": -110.0, "Result": "Loss", "Profit": -55, "Running Profit": -346.3465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 22.0, "Sport": "NFL", "Bet": "Harvey O19.5 rec yds", "Bet Type": "Total", "Bet Line": 19.5, "Bet Price": -110.0, "Result": "Win", "Profit": 20, "Running Profit": -326.3465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 23.0, "Sport": "NFL", "Bet": "coleman O18.5 rec yds", "Bet Type": "Total", "Bet Line": 18.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -23, "Running Profit": -349.3465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 22.4, "Sport": "NFL", "Bet": "Nix under 213.5", "Bet Type": "Total", "Bet Line": 213.5, "Bet Price": -112.0, "Result": "Loss", "Profit": -22.4, "Running Profit": -371.7465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 5.0, "Sport": "NFL", "Bet": "coleman td", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 550.0, "Result": "Win", "Profit": 27.5, "Running Profit": -344.2465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "nix/coleman/harvey", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 683.0, "Result": "Loss", "Profit": -20, "Running Profit": -364.2465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Bills ", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 130.0, "Result": "Loss", "Profit": -20, "Running Profit": -384.2465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 65.0, "Sport": "NFL", "Bet": "bills 7.5/seashawks 0", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -130.0, "Result": "Win", "Profit": 50, "Running Profit": -334.2465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 13.8, "Sport": "NFL", "Bet": "cook over 2.5 rec", "Bet Type": "Total", "Bet Line": 2.5, "Bet Price": 145.0, "Result": "Loss", "Profit": -13.8, "Running Profit": -348.0465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NFL", "Bet": "Tonges TD", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 388.0, "Result": "Loss", "Profit": -10, "Running Profit": -358.0465472, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 24.0, "Sport": "NFL", "Bet": "Tonges o33.5 yds", "Bet Type": "Total", "Bet Line": 33.5, "Bet Price": -118.0, "Result": "Win", "Profit": 20.33898305, "Running Profit": -337.7075641, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "", "Bet": "Tonges 60", "Bet Type": "Total", "Bet Line": 60.0, "Bet Price": 228.0, "Result": "Loss", "Profit": -10, "Running Profit": -347.7075641, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "", "Bet": "Tonges 53", "Bet Type": "Total", "Bet Line": 53.0, "Bet Price": 113.0, "Result": "Win", "Profit": 22.6, "Running Profit": -325.1075641, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Hutch/boutte/henry", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 683.0, "Result": "Win", "Profit": 136.6, "Running Profit": -188.5075641, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "", "Bet Amount": 10.0, "Sport": "NFL", "Bet": "Boutte td", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 500.0, "Result": "Win", "Profit": 50, "Running Profit": -138.5075641, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 24.0, "Sport": "", "Bet": "Boutee", "Bet Type": "Total", "Bet Line": 30.5, "Bet Price": -118.0, "Result": "Win", "Profit": 20.33898305, "Running Profit": -118.1685811, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 19.5, "Sport": "", "Bet": "Hutch", "Bet Type": "Total", "Bet Line": 30.5, "Bet Price": 105.0, "Result": "Win", "Profit": 20.475, "Running Profit": -97.69358107, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 22.0, "Sport": "", "Bet": "Henry ", "Bet Type": "Total", "Bet Line": 39.5, "Bet Price": -110.0, "Result": "Win", "Profit": 20, "Running Profit": -77.69358107, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Caesers", "Bet Amount": 56.0, "Sport": "", "Bet": "1H under pats", "Bet Type": "Total", "Bet Line": 20.0, "Bet Price": -112.0, "Result": "Loss", "Profit": -56, "Running Profit": -133.6935811, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Harvey o21.5 yds", "Bet Type": "Total", "Bet Line": 21.5, "Bet Price": 100.0, "Result": "Win", "Profit": 20, "Running Profit": -113.6935811, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 24.0, "Sport": "NFL", "Bet": "Henry o39.5 yds", "Bet Type": "Total", "Bet Line": 39.5, "Bet Price": -118.0, "Result": "Loss", "Profit": -24, "Running Profit": -137.6935811, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NFL", "Bet": "Harvey Henry Douglas", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 494.0, "Result": "Loss", "Profit": -10, "Running Profit": -147.6935811, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 10.0, "Sport": "NFL", "Bet": "Mims td", "Bet Type": "Total", "Bet Line": 10.0, "Bet Price": 625.0, "Result": "Loss", "Profit": -10, "Running Profit": -157.6935811, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Bryant td", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 420.0, "Result": "Loss", "Profit": 0.0, "Running Profit": -157.6935811, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 22.4, "Sport": "NFL", "Bet": "Walker under 82.5", "Bet Type": "Total", "Bet Line": 82.5, "Bet Price": -112.0, "Result": "Win", "Profit": 20, "Running Profit": -137.6935811, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 23.8, "Sport": "NFL", "Bet": "Adams over 47.5 yds", "Bet Type": "Total", "Bet Line": 47.5, "Bet Price": -118.0, "Result": "Win", "Profit": 20.16949153, "Running Profit": -117.5240895, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 22.4, "Sport": "NFL", "Bet": "Ferguson over 14.5 yds", "Bet Type": "Total", "Bet Line": 14.5, "Bet Price": -112.0, "Result": "Loss", "Profit": -22.4, "Running Profit": -139.9240895, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Ferg/adams/walker ", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 520.0, "Result": "Loss", "Profit": -20, "Running Profit": -159.9240895, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "Rams7.5/O42.5", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 130.0, "Result": "Win", "Profit": 26, "Running Profit": -133.9240895, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": 230.0, "Sport": "NFL", "Bet": "Broncos", "Bet Type": "Side", "Bet Line": 5.5, "Bet Price": -115.0, "Result": "Win", "Profit": 200, "Running Profit": 66.07591046, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 10.0, "Sport": "NFL", "Bet": "Darnold vs maye", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 110.0, "Result": "Loss", "Profit": -10, "Running Profit": 56.07591046, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "powers", "Sportsbook": "Prime", "Bet Amount": 50.5, "Sport": "NFL", "Bet": "2nd half over 23", "Bet Type": "Total", "Bet Line": 23.0, "Bet Price": -101.0, "Result": "Win", "Profit": 50, "Running Profit": 106.0759105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 24.75, "Sport": "NFL", "Bet": "May over 30.5 pass att", "Bet Type": "Total", "Bet Line": 30.5, "Bet Price": 101.0, "Result": "Win", "Profit": 24.9975, "Running Profit": 131.0734105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 23.0, "Sport": "NFL", "Bet": "henderson over 2.5 rec yds", "Bet Type": "Total", "Bet Line": 2.5, "Bet Price": -115.0, "Result": "Win", "Profit": 20, "Running Profit": 151.0734105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 22.8, "Sport": "NFL", "Bet": "henry over 37.5 rec yds", "Bet Type": "Total", "Bet Line": 37.5, "Bet Price": -114.0, "Result": "Loss", "Profit": -22.8, "Running Profit": 128.2734105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 22.0, "Sport": "NFL", "Bet": "walker under 72.5 rush yds", "Bet Type": "Total", "Bet Line": 72.5, "Bet Price": -110.0, "Result": "Loss", "Profit": -22, "Running Profit": 106.2734105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 5.0, "Sport": "NFL", "Bet": "Henry anytime td", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": 250.0, "Result": "Loss", "Profit": -5, "Running Profit": 101.2734105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 10.2, "Sport": "NFL", "Bet": "milton williams sack", "Bet Type": "Total", "Bet Line": 0.5, "Bet Price": 196.0, "Result": "Win", "Profit": 19.992, "Running Profit": 121.2654105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 55.0, "Sport": "NFL", "Bet": "seahawks ML/under 52.5", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": -110.0, "Result": "Win", "Profit": 50, "Running Profit": 171.2654105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 20.0, "Sport": "NFL", "Bet": "henderson O2.5/2ndH O23.5", "Bet Type": "Parlay", "Bet Line": 0.0, "Bet Price": 320.0, "Result": "Win", "Profit": 64, "Running Profit": 235.2654105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 32.5, "Sport": "NFL", "Bet": "2nd h higher scoring ", "Bet Type": "Total", "Bet Line": 0.0, "Bet Price": -130.0, "Result": "Win", "Profit": 25, "Running Profit": 260.2654105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 26.5, "Sport": "NFL", "Bet": "Over 1.5 int thrown", "Bet Type": "Total", "Bet Line": 1.5, "Bet Price": -106.0, "Result": "Win", "Profit": 25, "Running Profit": 285.2654105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "4/2/2025", "Account": "James", "Bet Description": "", "Source": "Powers", "Sportsbook": "MGM", "Bet Amount": 94.0, "Sport": "NCAAF", "Bet": "West Virginia under ", "Bet Type": "Total", "Bet Line": 5.5, "Bet Price": 115.0, "Result": "Win", "Profit": 108.1, "Running Profit": 174.1759105, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "4/12/2025", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 300.0, "Sport": "NCAAF", "Bet": "Tennessee under 9.5", "Bet Type": "Total", "Bet Line": 9.5, "Bet Price": -145.0, "Result": "Win", "Profit": 206.8965517, "Running Profit": 381.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/1/2025", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 100.0, "Sport": "NCAAF", "Bet": "Clemson win ACC", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 200.0, "Result": "Loss", "Profit": -100, "Running Profit": 281.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/5/2025", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 100.0, "Sport": "NCAAF", "Bet": "Memphis win American", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 600.0, "Result": "Loss", "Profit": -100, "Running Profit": 181.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/5/2025", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 100.0, "Sport": "NCAAF", "Bet": "James Madison win SBC", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 400.0, "Result": "Win", "Profit": 400, "Running Profit": 581.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/22/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 50.0, "Sport": "NCAAF", "Bet": "Kansas st win B12", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 600.0, "Result": "Loss", "Profit": -50, "Running Profit": 531.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/22/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 105.0, "Sport": "NCAAF", "Bet": "Kansas Under 7.5 wins", "Bet Type": "Side", "Bet Line": 7.5, "Bet Price": -105.0, "Result": "Win", "Profit": 100, "Running Profit": 631.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/22/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 122.0, "Sport": "NCAAF", "Bet": "Virginia Under 6.5 wins", "Bet Type": "Side", "Bet Line": 6.5, "Bet Price": -122.0, "Result": "Loss", "Profit": -122, "Running Profit": 509.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/22/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 50.0, "Sport": "NCAAF", "Bet": "Navy win American", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 450.0, "Result": "Loss", "Profit": -50, "Running Profit": 459.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/22/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 50.0, "Sport": "NCAAF", "Bet": "western kentucky win cusa", "Bet Type": "Side", "Bet Line": 0.0, "Bet Price": 490.0, "Result": "Loss", "Profit": -50, "Running Profit": 409.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/27/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 120.0, "Sport": "NCAAF", "Bet": "TCU Over 6.5", "Bet Type": "Total", "Bet Line": 6.5, "Bet Price": -120.0, "Result": "Win", "Profit": 100, "Running Profit": 509.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/27/2025", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 140.0, "Sport": "NCAAF", "Bet": "Air Force Over 5.5", "Bet Type": "Total", "Bet Line": 5.5, "Bet Price": -140.0, "Result": "Loss", "Profit": -140, "Running Profit": 369.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/27/2025", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 150.0, "Sport": "NCAAF", "Bet": "Colorado St Under 6.5", "Bet Type": "Total", "Bet Line": 6.5, "Bet Price": -150.0, "Result": "Win", "Profit": 100, "Running Profit": 469.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/27/2025", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 115.0, "Sport": "NCAAF", "Bet": "Arkansas St Under 5.5", "Bet Type": "Total", "Bet Line": 5.5, "Bet Price": -115.0, "Result": "Loss", "Profit": -115, "Running Profit": 354.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/27/2025", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 160.0, "Sport": "NCAAF", "Bet": "Bowling Green Under 6.5", "Bet Type": "Total", "Bet Line": 6.5, "Bet Price": -160.0, "Result": "Win", "Profit": 100, "Running Profit": 454.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/27/2025", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "Buffalo win Mac", "Bet Type": "", "Bet Line": "", "Bet Price": 700.0, "Result": "Loss", "Profit": -20, "Running Profit": 434.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "5/27/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 10.0, "Sport": "", "Bet": "Buffalo win Mac", "Bet Type": "", "Bet Line": "", "Bet Price": 800.0, "Result": "Loss", "Profit": -10, "Running Profit": 424.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 140.0, "Sport": "", "Bet": "Colorado under 6.5", "Bet Type": "Total", "Bet Line": "", "Bet Price": -140.0, "Result": "Win", "Profit": 100, "Running Profit": 524.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 130.0, "Sport": "", "Bet": "USC over 7.5", "Bet Type": "Total", "Bet Line": "", "Bet Price": -130.0, "Result": "Win", "Profit": 100, "Running Profit": 624.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "Bet365", "Bet Amount": 170.0, "Sport": "", "Bet": "Delaware under 5.5", "Bet Type": "Total", "Bet Line": "", "Bet Price": -170.0, "Result": "Loss", "Profit": -170, "Running Profit": 454.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "6/27/2025", "Account": "Ashlee", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 145.0, "Sport": "", "Bet": "Wazzu under 5.5", "Bet Type": "Total", "Bet Line": "", "Bet Price": -135.0, "Result": "Loss", "Profit": -145, "Running Profit": 309.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "7/17/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 160.0, "Sport": "", "Bet": "Syracuse Under 5.5", "Bet Type": "Total", "Bet Line": "", "Bet Price": -160.0, "Result": "Win", "Profit": 100, "Running Profit": 409.0724622, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "7/17/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fanatics", "Bet Amount": 18.0, "Sport": "", "Bet": "Syracuse Under 5.5", "Bet Type": "Total", "Bet Line": "", "Bet Price": -135.0, "Result": "Win", "Profit": 13.33333333, "Running Profit": 422.4057955, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "7/21/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 154.0, "Sport": "", "Bet": "Northwestern over 3.5", "Bet Type": "", "Bet Line": "", "Bet Price": -155.0, "Result": "Win", "Profit": 99.35483871, "Running Profit": 521.7606342, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "7/30/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 135.0, "Sport": "", "Bet": "South Carolina Under 7.5", "Bet Type": "", "Bet Line": "", "Bet Price": -135.0, "Result": "Win", "Profit": 100, "Running Profit": 621.7606342, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/1/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 88.0, "Sport": "", "Bet": "Liberty win CUSA", "Bet Type": "", "Bet Line": "", "Bet Price": 130.0, "Result": "Loss", "Profit": -88, "Running Profit": 533.7606342, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/1/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Hard Rock", "Bet Amount": 33.0, "Sport": "", "Bet": "Liberty win CUSA", "Bet Type": "", "Bet Line": "", "Bet Price": 125.0, "Result": "Loss", "Profit": -33, "Running Profit": 500.7606342, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/14/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Draft Kings", "Bet Amount": 145.0, "Sport": "", "Bet": "Oklahoma state under 3.5 conf wins", "Bet Type": "", "Bet Line": 3.5, "Bet Price": -145.0, "Result": "Win", "Profit": 100, "Running Profit": 600.7606342, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/14/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Prime", "Bet Amount": 30.0, "Sport": "", "Bet": "michigan under 8.5 wins", "Bet Type": "", "Bet Line": 8.5, "Bet Price": 166.0, "Result": "Loss", "Profit": -30, "Running Profit": 570.7606342, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "8/14/2025", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "MGM", "Bet Amount": 120.0, "Sport": "", "Bet": "Florida under 7.5 wins", "Bet Type": "", "Bet Line": 7.5, "Bet Price": -120.0, "Result": "Win", "Profit": 100, "Running Profit": 670.7606342, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "James", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 50.0, "Sport": "NCAAF", "Bet": "Utah win B12", "Bet Type": "", "Bet Line": 0.0, "Bet Price": 470.0, "Result": "Loss", "Profit": -50, "Running Profit": 620.7606342, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}, {"Date": "", "Account": "", "Bet Description": "", "Source": "", "Sportsbook": "Fan Duel", "Bet Amount": 20.0, "Sport": "NCAAF", "Bet": "illinois make playoff", "Bet Type": "", "Bet Line": 0.0, "Bet Price": 1800.0, "Result": "Loss", "Profit": -20, "Running Profit": 600.7606342, "Closing Line": "", "Closing Price": "", "CLV": "", "EV": "", "Notes": "", "CLV %": "", "#DIV/0!": "", "Wins": "", "Losses": "", "CLV +": "", "CLV -": "", "Bet Jack": ""}];
const BETTING_2025_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTmGvvkdhjSorHoTPbW5f33N6--AXLmWBLitZomgKejjOpo2aG6bL4UFtVfD3RFteCUNPEbDilnq2X1/pub?gid=1629429397&single=true&output=csv";
let bettingSeason = '2026';


function fmtPct(v) { return v==null ? '—' : (v*100).toFixed(1)+'%'; }
function fmtDate(s) { return new Date(s+'T00:00:00').toLocaleDateString(undefined, {month:'short', day:'numeric'}); }
function spreadText(g) {
  if (!g || g.projected_margin_home == null) return '—';
  const v = g.projected_margin_home;
  if (Math.abs(v) < 0.05) return 'PK';
  const favored = v > 0 ? g.home_team : g.away_team;
  return `${teamLabel(favored)} -${Math.abs(v).toFixed(1)}`;
}
function teamSpreadText(v) {
  if (v == null) return '—';
  return (v > 0 ? '+' : '') + v.toFixed(1);
}
function byId(id) { return document.getElementById(id); }
function navBtn(hash, label) {
  const active = location.hash === hash || (hash==='#/' && (!location.hash || location.hash==='#'));
  return `<button class="${active?'active':''}" onclick="location.hash='${hash}'">${label}</button>`;
}
function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
// Team image controls.
// Use "logo" after uploading a /logos folder, "helmet" to use /helmets, or "none" to hide images.
const TEAM_IMAGE_MODE = "logo";

const TEAM_IMAGE_FILE_OVERRIDES = {
  "Texas A&M": "texas-aandm"
};

// Only these darker/blue logos get the light badge.
// Most logos stay unboxed for a cleaner dark-mode look.
const LOGO_BADGE_TEAMS = new Set([
  "Air Force",
  "Boise State",
  "BYU",
  "Duke",
  "Georgia Tech",
  "Iowa",
  "Navy",
  "North Carolina",
  "North Dakota State",
  "Notre Dame",
  "Penn State",
  "Pittsburgh",
  "Rice",
  "Toledo",
  "Tulane",
  "UTEP",
  "Virginia",
  "Wake Forest",
  "West Virginia"
]);
function teamImageFileForTeam(t) {
  if (!t) return null;
  return TEAM_IMAGE_FILE_OVERRIDES[t.team] || t.slug;
}
function teamImageImg(name) {
  if (TEAM_IMAGE_MODE === "none") return '';
  const t = teamByName[String(name || '').toLowerCase()];
  if (!t) return '';
  const folder = TEAM_IMAGE_MODE === "helmet" ? "helmets" : "logos";
  const file = teamImageFileForTeam(t);
  const badgeClass = (TEAM_IMAGE_MODE === "logo" && LOGO_BADGE_TEAMS.has(t.team)) ? " needs-badge" : "";
  return `<span class="team-logo-wrap${badgeClass}"><img class="team-logo" src="${folder}/${file}.png" alt="" loading="lazy" onerror="this.closest('.team-logo-wrap').style.display='none'"></span>`;
}
function teamLabel(name) {
  const safe = escapeHtml(name || '—');
  const t = teamByName[String(name || '').toLowerCase()];
  if (!t) return safe;
  return `<span class="team-with-logo">${teamImageImg(name)}<span>${safe}</span></span>`;
}
function linkTeam(name) {
  const t = teamByName[String(name || '').toLowerCase()];
  return t ? `<span class="linkish team-with-logo" onclick="location.hash='#team/${t.slug}'">${teamImageImg(name)}<span>${escapeHtml(name)}</span></span>` : escapeHtml(name || '—');
}

function linkTeamWithComboRank(name) {
  const t = teamByName[String(name || '').toLowerCase()];
  if (!t) return escapeHtml(name || '—');
  return `${linkTeam(name)} <span class="small">(#${t.rank})</span>`;
}

function americanOddsFromProb(p) {
  if (p == null || !isFinite(p) || p <= 0) return '—';
  if (p >= 1) return '-∞';
  const pct = p * 100;
  if (pct < 50) return '+' + Math.round((100 - pct) * 100 / pct);
  return '-' + Math.round(pct * 100 / (100 - pct));
}
function americanOddsNumberFromProb(p) {
  if (p == null || !isFinite(p) || p <= 0) return null;
  if (p >= 1) return -999999;
  const pct = Number(p) * 100;
  if (pct < 50) return Math.round((100 - pct) * 100 / pct);
  return -Math.round(pct * 100 / (100 - pct));
}
function fmtSOS(v) {
  return v == null || !isFinite(v) ? '—' : Number(v).toFixed(1);
}

function fmtSigned(v) {
  if (v == null || !isFinite(v)) return '—';
  const n = Number(v);
  return (n > 0 ? '+' : '') + n.toFixed(1);
}
function fmtSignedClass(v) {
  if (v == null || !isFinite(v) || Math.abs(Number(v)) < 0.05) return '';
  return Number(v) > 0 ? 'pos' : 'neg';
}


// Market futures / win-total helpers. Data is embedded by build_site_from_workbook_safe.py.
const marketBestRows = Array.isArray(DB.market_futures_best_prices) ? DB.market_futures_best_prices : [];
const marketEdgeRows = Array.isArray(DB.market_futures_edges) ? DB.market_futures_edges : [];
const marketWinRawRows = Array.isArray(DB.market_win_totals_raw) ? DB.market_win_totals_raw : [];
const marketFuturesRawRows = Array.isArray(DB.market_conference_futures_raw) ? DB.market_conference_futures_raw : [];
const MARKET_BOOKS = [
  {key:'dk', label:'DK', names:['draftkings','draft kings','dk']},
  {key:'fd', label:'FD', names:['fanduel','fan duel','fd']},
  {key:'mgm', label:'MGM', names:['betmgm','bet mgm','mgm']},
  {key:'caesars', label:'Caesars', names:['caesars','caesar','czr']},
];
function normMarketTeamName(name) {
  let s = String(name || '').toLowerCase().replace(/&/g,'and').replace(/[^a-z0-9]+/g,' ').trim();
  // Cross-book aliases seen in Action Network / sportsbook pulls. This is intentionally
  // applied before grouping rows so abbreviated book rows merge into the dashboard team row.
  const aliases = {

    'app state': 'appalachian state',
    'appalachian st': 'appalachian state',
    'arkansas st': 'arkansas state',
    'c michigan': 'central michigan',
    'central michigan chippewas': 'central michigan',
    'coastal car': 'coastal carolina',
    'e carolina': 'east carolina',
    'e michigan': 'eastern michigan',
    'fiu': 'florida international',
    'fl atlantic': 'florida atlantic',
    'ga southern': 'georgia southern',
    'jmu': 'james madison',
    'jax state': 'jacksonville state',
    'kennesaw st': 'kennesaw state',
    'la tech': 'louisiana tech',
    'la monroe': 'ul monroe',
    'ulm': 'ul monroe',
    'middle tenn': 'middle tennessee',
    'mississippi st': 'mississippi state',
    'missouri st': 'missouri state',
    'n illinois': 'northern illinois',
    'n mexico st': 'new mexico state',
    'nd state': 'north dakota state',
    's alabama': 'south alabama',
    's florida': 'south florida',
    'sac state': 'sacramento state',
    'san jose st': 'san jose state',
    'uconn': 'connecticut',
    'umass': 'massachusetts',
    'w kentucky': 'western kentucky',
    'w michigan': 'western michigan',
    'miami oh': 'miami-oh',
    'ok state': 'oklahoma state',
    'okla state': 'oklahoma state',
    'oklahoma st': 'oklahoma state',
    'k state': 'kansas state',
    'kansas st': 'kansas state',
    'ga tech': 'georgia tech',
    'georgia tech yellow jackets': 'georgia tech',
    's carolina': 'south carolina',
    'south carolina gamecocks': 'south carolina',
    'unc': 'north carolina',
    'n carolina': 'north carolina',
    'north carolina tar heels': 'north carolina',
    'michigan st': 'michigan state',
    'michigan state spartans': 'michigan state',
    'miami florida': 'miami fl',
    'miami fla': 'miami fl',
    'miami fl': 'miami fl',
    'miami fl hurricanes': 'miami fl'
  };
  if (aliases[s]) return aliases[s];
  s = s.replace(/\bst\.?\b/g, 'state');
  return (aliases[s] || s).replace(/\s+/g,' ');
}

function normBookName(book) {
  const s = String(book || '').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  const found = MARKET_BOOKS.find(b => b.names.includes(s));
  return found ? found.key : s.replace(/\s+/g,'_');
}
function bookLabelFromKey(key) {
  const found = MARKET_BOOKS.find(b => b.key === key || b.names.includes(String(key || '').toLowerCase()));
  return found ? found.label : String(key || '—');
}
function marketBookCount(row) {
  const raw = String((row && row.books_available) || '');
  if (!raw.trim()) return 0;
  return raw.split(',').map(x => x.trim()).filter(Boolean).length;
}
function marketRowScore(row) {
  if (!row) return -999;
  let score = marketBookCount(row) * 10;
  if (row.market_win_total != null && row.market_win_total !== '') score += 3;
  if (row.best_over_odds != null || row.best_under_odds != null) score += 3;
  if (row.best_title_odds != null || row.market_implied_title_prob != null) score += 3;
  if (row.conference) score += 1;
  return score;
}
function marketRowTeamKey(r) {
  // Prefer explicit canonical fields, but always run through the same market alias normalizer.
  // Some 8am pulls have team_norm values like "app state", "c michigan", "w michigan";
  // those still need alias expansion to match site teams like Appalachian State.
  const raw = r && (r.canonical_team || r.team_norm || r.team);
  return normMarketTeamName(raw);
}
function buildMarketRowsByTeam(rows) {
  const out = {};
  (rows || []).forEach(r => {
    const k = marketRowTeamKey(r);
    if (!k) return;
    if (!out[k] || marketRowScore(r) >= marketRowScore(out[k])) out[k] = r;
  });
  return out;
}
const marketBestByTeam = buildMarketRowsByTeam(marketBestRows);
const marketEdgeByTeam = buildMarketRowsByTeam(marketEdgeRows);
function groupMarketRowsByTeam(rows) {
  const out = {};
  (rows || []).forEach(r => {
    const k = marketRowTeamKey(r);
    if (!k) return;
    if (!out[k]) out[k] = [];
    out[k].push(r);
  });
  return out;
}
const marketWinRawByTeam = groupMarketRowsByTeam(marketWinRawRows);
const marketFuturesRawByTeam = groupMarketRowsByTeam(marketFuturesRawRows);

function marketLatestPullLabel(rows) {
  const vals = (rows || [])
    .map(r => r && (r.pulled_at || r.snapshot_date || r.latest_snapshot_date))
    .filter(Boolean)
    .sort();
  if (!vals.length) return '';
  const raw = vals[vals.length - 1];
  const d = new Date(raw);
  if (!isNaN(d.getTime())) {
    return d.toLocaleDateString(undefined, {month:'short', day:'numeric'});
  }
  const m = String(raw).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) {
    const dd = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    return dd.toLocaleDateString(undefined, {month:'short', day:'numeric'});
  }
  return String(raw);
}
const marketWinLatestPullLabel = marketLatestPullLabel(marketWinRawRows);
const marketFuturesLatestPullLabel = marketLatestPullLabel(marketFuturesRawRows);



const MARKET_TEAM_ALIASES_EXTRA = {

  "app state": "appalachian state",

  "arkansas st": "arkansas state",

  "c michigan": "central michigan",

  "coastal car": "coastal carolina",

  "e carolina": "east carolina",

  "e michigan": "eastern michigan",

  "fiu": "florida international",

  "fl atlantic": "florida atlantic",

  "ga southern": "georgia southern",

  "ga tech": "georgia tech",

  "jmu": "james madison",

  "jax state": "jacksonville state",

  "k state": "kansas state",

  "kennesaw st": "kennesaw state",

  "la tech": "louisiana tech",

  "la monroe": "ul monroe",

  "ul monroe": "ul monroe",

  "middle tenn": "middle tennessee",

  "mississippi st": "mississippi state",

  "missouri st": "missouri state",

  "n illinois": "northern illinois",

  "n mexico st": "new mexico state",

  "nd state": "north dakota state",

  "ok state": "oklahoma state",

  "s alabama": "south alabama",

  "s carolina": "south carolina",

  "s florida": "south florida",

  "sac state": "sacramento state",

  "san jose st": "san jose state",

  "uconn": "connecticut",

  "umass": "massachusetts",

  "unc": "north carolina",

  "w kentucky": "western kentucky",

  "w michigan": "western michigan",

  "miami oh": "miami-oh",

  "miami (oh)": "miami-oh",

  "michigan st": "michigan state"

};

function marketAliasNormName(name){

  let s = String(name || '').toLowerCase();

  s = s.replace(/&/g, 'and');

  s = s.replace(/[’']/g, '');

  s = s.replace(/[^a-z0-9]+/g, ' ').trim().replace(/\s+/g, ' ');

  return MARKET_TEAM_ALIASES_EXTRA[s] || s;

}


function rawWinRowsForTeam(teamName) { return marketWinRawByTeam[normMarketTeamName(teamName)] || []; }
function rawFuturesRowsForTeam(teamName) { return marketFuturesRawByTeam[normMarketTeamName(teamName)] || []; }
function marketForTeam(teamName) {
  const key = normMarketTeamName(teamName);
  return marketEdgeByTeam[key] || marketBestByTeam[key] || null;
}
function fmtOdds(v) {
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  const n = Math.round(Number(v));
  return n > 0 ? '+' + n : String(n);
}
function fmtWins(v) {
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  return Number(v).toFixed(2).replace(/\.00$/,'');
}
function fmtMarketPct(v) {
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  const n = Number(v);
  return (n > 1 ? n : n * 100).toFixed(1) + '%';
}
function marketWinLine(m) {
  if (!m) return '—';
  return m.market_win_total ?? m.win_total ?? '—';
}
function projectedWinsForMarket(teamName, m) {
  const t = teamByName[String(teamName || '').toLowerCase()];
  return (m && m.projected_wins != null) ? Number(m.projected_wins) : (t ? Number(t.avg_total_wins) : null);
}
function projectedTitleProbForMarket(teamName, m) {
  const t = teamByName[String(teamName || '').toLowerCase()];
  return (m && m.projected_conf_title_prob != null) ? Number(m.projected_conf_title_prob) : (t ? Number(t.conference_title_pct) : null);
}
function winEdgeForMarket(teamName, m) {
  if (!m) return null;
  if (m.win_total_edge != null && isFinite(Number(m.win_total_edge))) return Number(m.win_total_edge);
  const proj = projectedWinsForMarket(teamName, m);
  const line = Number(marketWinLine(m));
  if (!isFinite(proj) || !isFinite(line)) return null;
  return proj - line;
}
function titleEdgeForMarket(teamName, m) {
  if (!m) return null;
  if (m.title_edge != null && isFinite(Number(m.title_edge))) return Number(m.title_edge);
  const proj = projectedTitleProbForMarket(teamName, m);
  const market = Number(m.market_implied_title_prob);
  if (!isFinite(proj) || !isFinite(market)) return null;
  return proj - market;
}
function oddsEqual(a,b) {
  return a != null && b != null && isFinite(Number(a)) && isFinite(Number(b)) && Math.round(Number(a)) === Math.round(Number(b));
}
function isBestBook(rowBook, bestBook) {
  return normBookName(rowBook) === normBookName(bestBook);
}
function bestBadge(isBest) { return ''; }
function renderOddsCell(odds, isBest) {
  return `<span class="${isBest ? 'market-best' : ''}">${fmtOdds(odds)}</span>${bestBadge(isBest)}`;
}
function renderWinBookCell(row, m) {
  if (!row) return '—';
  const overBest = oddsEqual(row.over_odds, m && m.best_over_odds) && isBestBook(row.book, m && m.best_over_book);
  const underBest = oddsEqual(row.under_odds, m && m.best_under_odds) && isBestBook(row.book, m && m.best_under_book);
  return `<div>${fmtWins(row.win_total)}</div><div class="small">O ${renderOddsCell(row.over_odds, overBest)}</div><div class="small">U ${renderOddsCell(row.under_odds, underBest)}</div>`;
}
function renderTitleBookCell(row, m) {
  if (!row) return '—';
  const titleBest = oddsEqual(row.american_odds, m && m.best_title_odds) && isBestBook(row.book, m && m.best_title_book);
  return renderOddsCell(row.american_odds, titleBest);
}
function bookRowsByKey(rows) {
  const out = {};
  (rows || []).forEach(r => { out[normBookName(r.book)] = r; });
  return out;
}
function renderAllBookTables(teamName, m) {
  const winRows = rawWinRowsForTeam(teamName);
  const futRows = rawFuturesRowsForTeam(teamName);
  const winByBook = bookRowsByKey(winRows);
  const futByBook = bookRowsByKey(futRows);
  if (!winRows.length && !futRows.length) return '';
  return `<div class="market-book-grid">
    <div class="small muted" style="margin-bottom:6px">All sportsbook prices. Green badge marks the best available price.</div>
    ${winRows.length ? `<div class="small" style="font-weight:800;margin:8px 0 4px">Win Total</div>
      <table><thead><tr><th>Book</th><th>Line</th><th>Over</th><th>Under</th></tr></thead><tbody>
        ${MARKET_BOOKS.map(b => {
          const r = winByBook[b.key];
          if (!r) return `<tr><td>${sportsbookLogo(b.label)}</td><td colspan="3" class="muted">—</td></tr>`;
          const overBest = oddsEqual(r.over_odds, m && m.best_over_odds) && isBestBook(r.book, m && m.best_over_book);
          const underBest = oddsEqual(r.under_odds, m && m.best_under_odds) && isBestBook(r.book, m && m.best_under_book);
          return `<tr><td>${sportsbookLogo(b.label)}</td><td>${fmtWins(r.win_total)}</td><td>${renderOddsCell(r.over_odds, overBest)}</td><td>${renderOddsCell(r.under_odds, underBest)}</td></tr>`;
        }).join('')}
      </tbody></table>` : ''}
    ${futRows.length ? `<div class="small" style="font-weight:800;margin:12px 0 4px">Conference Title</div>
      <table><thead><tr><th>Book</th><th>Odds</th><th>Implied %</th></tr></thead><tbody>
        ${MARKET_BOOKS.map(b => {
          const r = futByBook[b.key];
          if (!r) return `<tr><td>${sportsbookLogo(b.label)}</td><td colspan="2" class="muted">—</td></tr>`;
          const titleBest = oddsEqual(r.american_odds, m && m.best_title_odds) && isBestBook(r.book, m && m.best_title_book);
          return `<tr><td>${sportsbookLogo(b.label)}</td><td>${renderOddsCell(r.american_odds, titleBest)}</td><td>${fmtMarketPct(americanOddsToProb(Number(r.american_odds)))}</td></tr>`;
        }).join('')}
      </tbody></table>` : ''}
  </div>`;
}
function americanOddsToProb(odds) {
  const o = Number(odds);
  if (!isFinite(o) || o === 0) return null;
  return o > 0 ? 100 / (o + 100) : Math.abs(o) / (Math.abs(o) + 100);
}

function sportsbookLogo(book) {
  const raw = String(book || '').trim();
  const b = raw.toLowerCase();

  let src = '';
  let label = raw || 'Book';

  if (b.includes('fanduel') || b === 'fd' || b === 'fan duel') {
    src = 'logos/books/fanduel.png';
    label = 'FanDuel';
  } else if (b.includes('draftkings') || b === 'dk' || b === 'draft kings') {
    src = 'logos/books/draftkings.png';
    label = 'DraftKings';
  } else if (b.includes('betmgm') || b.includes('mgm')) {
    src = 'logos/books/betmgm.png';
    label = 'BetMGM';
  } else if (b.includes('caesars') || b.includes('caesar') || b === 'cz') {
    src = 'logos/books/caesars.png';
    label = 'Caesars';
  }

  if (!src) return raw || '—';

  return `<span class="sportsbook-logo-wrap" title="${label}">
    <img class="sportsbook-logo" src="${src}" alt="${label}">
  </span>`;
}

function sportsbookHeaderLogo(book, subLabel) {
  let pullLabel = '';
  try {
    const rows = String(subLabel || '').toLowerCase().includes('title')
      ? (marketFuturesRawRows || [])
      : (marketWinRawRows || []);
    const bookKey = normBookName(book);
    const vals = rows
      .filter(r => normBookName(r.book) === bookKey)
      .map(r => r.pulled_at || r.snapshot_date || r.latest_snapshot_date)
      .filter(Boolean)
      .sort();

    if (vals.length) {
      const raw = vals[vals.length - 1];
      const d = new Date(raw);
      if (!isNaN(d.getTime())) {
        pullLabel = d.toLocaleDateString(undefined, {month:'short', day:'numeric'});
      } else {
        const m = String(raw).match(/^(\\d{4})-(\\d{2})-(\\d{2})/);
        if (m) {
          const dd = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
          pullLabel = dd.toLocaleDateString(undefined, {month:'short', day:'numeric'});
        }
      }
    }
  } catch(e) {}

  const pullHtml = pullLabel ? `<div class="sportsbook-header-date">Last pull: ${pullLabel}</div>` : '';
  return `<div class="sportsbook-header-logo">${sportsbookLogo(book)}<div class="sportsbook-header-sub">${subLabel || ''}</div>${pullHtml}</div>`;
}

function replaceSportsbookNamesWithLogos(html) {
  return String(html || '')
    .replaceAll('FanDuel', sportsbookLogo('FanDuel'))
    .replaceAll('DraftKings', sportsbookLogo('DraftKings'))
    .replaceAll('BetMGM', sportsbookLogo('BetMGM'))
    .replaceAll('Caesars', sportsbookLogo('Caesars'));
}

function renderMarketTeamCard(teamName) {
  const m = marketForTeam(teamName);
  const winRows = rawWinRowsForTeam(teamName);
  const futRows = rawFuturesRowsForTeam(teamName);
  const projWins = projectedWinsForMarket(teamName, m);
  const winEdge = winEdgeForMarket(teamName, m);
  const projTitle = projectedTitleProbForMarket(teamName, m);
  const titleEdge = titleEdgeForMarket(teamName, m);
  if (!m && !winRows.length && !futRows.length) {
    return `<div class="card market-projection-card"><div class="section-title">Market vs Projection</div><div class="small muted">No market futures/win-total data loaded yet for ${escapeHtml(teamName)}.</div></div>`;
  }

  const titleEdgeClass = titleEdge == null ? '' : (titleEdge > 0 ? 'pos' : titleEdge < 0 ? 'neg' : '');
  const titleEdgeText = titleEdge == null ? '—' : fmtMarketPct(titleEdge);

  return `<div class="card market-projection-card"><div class="section-title">Market vs Projection</div>
    <div class="market-compact">
      <div class="market-compact-block">
        <div class="market-compact-title">Win Total</div>
        <div class="market-compact-grid">
          <div class="market-compact-metric"><div class="label">Projected</div><div class="value">${fmtWins(projWins)}</div></div>
          <div class="market-compact-metric"><div class="label">Market</div><div class="value">${marketWinLine(m)}</div></div>
          <div class="market-compact-metric"><div class="label">Edge</div><div class="value ${fmtSignedClass(winEdge)}">${fmtSigned(winEdge)}</div></div>
        </div>
        <div class="market-compact-lines">
          <div class="market-compact-line"><span class="label">Best Over</span><strong>${fmtOdds(m && m.best_over_odds)}</strong> <span class="small">${sportsbookLogo((m && m.best_over_book) || '')}</span></div>
          <div class="market-compact-line"><span class="label">Best Under</span><strong>${fmtOdds(m && m.best_under_odds)}</strong> <span class="small">${sportsbookLogo((m && m.best_under_book) || '')}</span></div>
        </div>
      </div>

      <div class="market-compact-block">
        <div class="market-compact-title">Conference Title</div>
        <div class="market-compact-grid">
          <div class="market-compact-metric"><div class="label">Projected</div><div class="value">${fmtMarketPct(projTitle)}</div></div>
          <div class="market-compact-metric"><div class="label">Market</div><div class="value">${fmtMarketPct(m && m.market_implied_title_prob)}</div></div>
          <div class="market-compact-metric"><div class="label">Edge</div><div class="value ${titleEdgeClass}">${titleEdgeText}</div></div>
        </div>
        <div class="market-compact-lines">
          <div class="market-compact-line"><span class="label">Best Odds</span><strong>${fmtOdds(m && m.best_title_odds)}</strong> <span class="small">${sportsbookLogo((m && m.best_title_book) || '')}</span></div>
          <div class="market-compact-line market-books"><span class="label">Books</span>${escapeHtml((m && m.books_available) || '—')}</div>
        </div>
      </div>
    </div>
  </div>`;
}
function compactWinBooks(team, m) {
  const by = bookRowsByKey(rawWinRowsForTeam(team));
  return MARKET_BOOKS.map(b => `<td>${renderWinBookCell(by[b.key], m)}</td>`).join('');
}
function compactTitleBooks(team, m) {
  const by = bookRowsByKey(rawFuturesRowsForTeam(team));
  return MARKET_BOOKS.map(b => `<td>${renderTitleBookCell(by[b.key], m)}</td>`).join('');
}
function renderConferenceMarketTable(confName, teams) {
  const rows = teams.map(t => ({team:t.team, t, m:marketForTeam(t.team), winRows:rawWinRowsForTeam(t.team), futRows:rawFuturesRowsForTeam(t.team)})).filter(x => x.m || x.winRows.length || x.futRows.length);
  if (!rows.length) {
    return `<div class="card" style="margin-top:16px"><div class="section-title">Market Futures / Win Totals</div><div class="small muted">No market futures or win-total rows loaded yet for ${escapeHtml(confName)}.</div></div>`;
  }
  rows.sort((a,b) => {
    const ae = titleEdgeForMarket(a.team, a.m); const be = titleEdgeForMarket(b.team, b.m);
    if (ae != null || be != null) return (be ?? -999) - (ae ?? -999);
    return (b.t.conference_title_pct || 0) - (a.t.conference_title_pct || 0);
  });
  return `<div class="card" style="margin-top:16px"><div class="section-title">Market Futures / Win Totals</div>
    <div style="overflow:auto"><table><thead>
      <tr><th rowspan="2">Team</th><th rowspan="2">Proj Wins</th><th rowspan="2">Consensus Market Wins</th><th rowspan="2">Win Edge</th><th colspan="4">Win Total Prices</th><th rowspan="2">Proj Title %</th><th rowspan="2">Best Title</th><th colspan="4">Conference Title Odds</th><th rowspan="2">Title Edge</th></tr>
      <tr>${MARKET_BOOKS.map(b=>`<th>${b.label}</th>`).join('')}${MARKET_BOOKS.map(b=>`<th>${b.label}</th>`).join('')}</tr>
    </thead><tbody>
      ${rows.map(({team,t,m}) => {
        const winEdge = winEdgeForMarket(team,m);
        const titleEdge = titleEdgeForMarket(team,m);
        return `<tr>
          <td>${linkTeam(team)}</td>
          <td>${fmtWins(projectedWinsForMarket(team,m))}</td>
          <td>${marketWinLine(m)}</td>
          <td class="${fmtSignedClass(winEdge)}">${fmtSigned(winEdge)}</td>
          ${compactWinBooks(team,m)}
          <td>${fmtMarketPct(projectedTitleProbForMarket(team,m))}</td>
          <td>${fmtOdds(m && m.best_title_odds)} <span class="small">${sportsbookLogo((m && m.best_title_book) || '')}</span></td>
          ${compactTitleBooks(team,m)}
          <td class="${titleEdge == null ? '' : (titleEdge > 0 ? 'pos' : titleEdge < 0 ? 'neg' : '')}">${titleEdge == null ? '—' : fmtMarketPct(titleEdge)}</td>
        </tr>`;
      }).join('')}
    </tbody></table></div>
  </div>`;
}


let marketBoardSortState = {key:'win_edge', dir:'desc'};


const winMovementRows = DB.market_win_totals_movement || [];
const futuresMovementRows = DB.market_conference_futures_movement || [];
function normMovementTeamName(name) { return normMarketTeamName(name); }
function movementKey(parts) {
  return parts.map((x, i) => {
    if (i === 0) return normMarketTeamName(x);
    if (i === parts.length - 1) return normBookName(x);
    return String(x || '').toLowerCase().trim();
  }).join('|');
}
const winMovementByTeamBook = Object.fromEntries(winMovementRows.map(r => [movementKey([normMarketTeamName(r.team), normBookName(r.book)]), r]));
const futuresMovementByTeamConfBook = Object.fromEntries(futuresMovementRows.map(r => [movementKey([r.team, r.conference, r.book]), r]));
function winMovementFor(team, book) {
  return winMovementByTeamBook[movementKey([normMarketTeamName(team), normBookName(book)])] || null;
}
function titleMovementFor(team, conf, book) {
  return futuresMovementByTeamConfBook[movementKey([team, conf, book])] || null;
}

const winRecentMovementRows = DB.market_win_totals_recent_movement || [];
const futuresRecentMovementRows = DB.market_conference_futures_recent_movement || [];
const winRecentByTeamBook = Object.fromEntries(winRecentMovementRows.map(r => [movementKey([normMarketTeamName(r.team), normBookName(r.book)]), r]));
const futuresRecentByTeamConfBook = Object.fromEntries(futuresRecentMovementRows.map(r => [movementKey([r.team, r.conference, r.book]), r]));
function winRecentFor(team, book) {
  return winRecentByTeamBook[movementKey([normMarketTeamName(team), normBookName(book)])] || null;
}
function titleRecentFor(team, conf, book) {
  return futuresRecentByTeamConfBook[movementKey([team, conf, book])] || null;
}
function shortDateText(raw) {
  if (!raw) return '';
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return String(raw);
  return d.toLocaleDateString([], {month:'short', day:'numeric'});
}
function latestPullChip(prevVal, currentVal, kind='odds', label='Last pull', prevDate='') {
  if (prevVal == null || currentVal == null || prevVal === '' || currentVal === '') return '';
  const prevN = Number(prevVal), curN = Number(currentVal);
  if (!isFinite(prevN) || !isFinite(curN)) return '';
  const fmt = kind === 'wins' ? fmtMoveWins : fmtMoveOdds;
  const pTxt = fmt(prevN), cTxt = fmt(curN);
  const dateTxt = prevDate ? ` since ${shortDateText(prevDate)}` : '';
  if (prevN === curN) return `<span class="market-latest-current no-move" title="${escapeHtml(label + dateTxt)}"><span class="market-move-label">Last</span> no move</span>`;
  const cls = curN > prevN ? 'move-up' : 'move-down';
  return `<span class="market-latest-current ${cls}" title="${escapeHtml(label + dateTxt)}"><span class="market-move-label">Last</span> ${pTxt} → ${cTxt}</span>`;
}
function winRecentSummary(team, book, side) {
  const r = winRecentFor(team, book);
  if (!r) return '';
  if (side === 'over') return latestPullChip(r.previous_over_odds, r.current_over_odds, 'odds', 'Over odds: previous pull → latest pull', r.previous_snapshot_date);
  if (side === 'under') return latestPullChip(r.previous_under_odds, r.current_under_odds, 'odds', 'Under odds: previous pull → latest pull', r.previous_snapshot_date);
  const line = latestPullChip(r.previous_win_total, r.current_win_total, 'wins', 'Win total: previous pull → latest pull', r.previous_snapshot_date);
  const over = latestPullChip(r.previous_over_odds, r.current_over_odds, 'odds', 'Over odds: previous pull → latest pull', r.previous_snapshot_date);
  const under = latestPullChip(r.previous_under_odds, r.current_under_odds, 'odds', 'Under odds: previous pull → latest pull', r.previous_snapshot_date);
  return [line, over ? over.replace('<span class="market-move-label">Last</span>', '<span class="market-move-label">O</span>') : '', under ? under.replace('<span class="market-move-label">Last</span>', '<span class="market-move-label">U</span>') : ''].filter(Boolean).join('');
}
function titleRecentSummary(team, conf, book) {
  const r = titleRecentFor(team, conf, book);
  if (!r) return '';
  return latestPullChip(r.previous_american_odds, r.current_american_odds, 'odds', 'Title odds: previous pull → latest pull', r.previous_snapshot_date);
}
function openWinSummary(team, book) {
  const r = winMovementFor(team, book);
  if (!r) return '';
  const line = openToCurrentChip(r.opening_win_total, r.current_win_total, 'wins');
  const over = openToCurrentChip(r.opening_over_odds, r.current_over_odds, 'odds');
  const under = openToCurrentChip(r.opening_under_odds, r.current_under_odds, 'odds');
  return [line, over ? over.replace('Open', 'O open') : '', under ? under.replace('Open', 'U open') : ''].filter(Boolean).join('');
}
function openTitleSummary(team, conf, book) {
  const r = titleMovementFor(team, conf, book);
  if (!r) return '';
  return openToCurrentChip(r.opening_american_odds, r.current_american_odds, 'odds');
}
function bestWinMovementForSide(r, side) {
  const book = side === 'over' ? r.best_over_book : r.best_under_book;
  if (!book) return null;
  return winMovementFor(r.team, book);
}
function bestWinRecentForSide(r, side) {
  const book = side === 'over' ? r.best_over_book : r.best_under_book;
  if (!book) return null;
  return winRecentFor(r.team, book);
}

function bestWinMovementForTeam(team, m) {
  if (!m) return null;
  return winMovementFor(team, m.best_over_book) || winMovementFor(team, m.best_under_book) || null;
}
function bestTitleMovementForTeam(team, conf, m) {
  if (!m || !m.best_title_book) return null;
  return titleMovementFor(team, conf, m.best_title_book) || null;
}
function fmtOddsMove(v) {
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  const n = Math.round(Number(v));
  return n > 0 ? '+' + n : String(n);
}
function fmtLineMove(v) {
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  const n = Number(v);
  const s = n > 0 ? '+' : '';
  return s + n.toFixed(1).replace(/\.0$/,'');
}
function movementBadge(value, type='odds') {
  if (value == null || value === '' || !isFinite(Number(value))) return '<span class="muted">—</span>';
  const n = Number(value);
  const cls = n > 0 ? 'pos' : n < 0 ? 'neg' : 'muted';
  const txt = type === 'line' ? fmtLineMove(n) : fmtOddsMove(n);
  return `<span class="${cls}">${txt}</span>`;
}

function movementArrow(value, type='odds', label='Move') {
  if (value == null || value === '' || !isFinite(Number(value))) return '<span class="market-move market-move-flat">↔ 0</span>';
  const n = Number(value);
  const cls = n > 0 ? 'market-move-up' : n < 0 ? 'market-move-down' : 'market-move-flat';
  const arrow = n > 0 ? '▲' : n < 0 ? '▼' : '↔';
  const txt = type === 'line' ? fmtLineMove(n) : fmtOddsMove(n);
  return `<span class="market-move ${cls}" title="${escapeHtml(label)}">${arrow} ${txt}</span>`;
}

function firstWinTotalSnapshotDate() {
  const rows = DB.market_win_totals_movement || [];
  let best = null;

  rows.forEach(r => {
    const raw = r.first_snapshot_date || r.snapshot_date || '';
    if (!raw) return;
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return;
    if (!best || d < best) best = d;
  });

  return best;
}

function formatShortDate(d) {
  if (!d || Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function bestWinHeader(label) {
  const d = firstWinTotalSnapshotDate();
  const txt = d ? `Line opened: ${formatShortDate(d)}` : 'Line opened: —';
  return `${label}<div class="market-header-open-date">${txt}</div>`;
}

function openCurrentOddsLabel(openOdds, currentOdds, label='Open') {
  if (openOdds == null || currentOdds == null || openOdds === '' || currentOdds === '') {
    return '<span class="market-move market-move-flat">Open —</span>';
  }
  const openN = Number(openOdds);
  const curN = Number(currentOdds);
  if (!isFinite(openN) || !isFinite(curN)) return '<span class="market-move market-move-flat">Open —</span>';

  const cls = curN > openN ? 'market-move-up' : curN < openN ? 'market-move-down' : 'market-move-flat';
  const title = `${label}: first captured pull → latest captured pull`;
  if (curN === openN) {
    return `<span class="market-move ${cls}" title="${escapeHtml(title)}">Open ${fmtOdds(openN)}</span>`;
  }
  return `<span class="market-move ${cls}" title="${escapeHtml(title)}">${fmtOdds(openN)} → ${fmtOdds(curN)}</span>`;
}
function marketTotalCell(r) {
  const total = r.market_total == null ? '—' : fmtWins(r.market_total);
  return `<div class="market-main">${total}</div>`;
}
function bestWinTotalForSide(r, side) {
  if (!r) return null;
  const targetBook = side === 'over' ? r.best_over_book : r.best_under_book;
  const targetOdds = side === 'over' ? r.best_over_odds : r.best_under_odds;
  if (!targetBook || targetOdds == null || targetOdds === '' || !isFinite(Number(targetOdds))) return null;
  const rows = rawWinRowsForTeam(r.team);
  const found = rows.find(row => {
    const rowOdds = side === 'over' ? row.over_odds : row.under_odds;
    return isBestBook(row.book, targetBook) && oddsEqual(rowOdds, targetOdds) && row.win_total != null && isFinite(Number(row.win_total));
  });
  return found ? Number(found.win_total) : null;
}
function sameWinTotalForBestOverUnder(r) {
  const overTotal = bestWinTotalForSide(r, 'over');
  const underTotal = bestWinTotalForSide(r, 'under');
  return overTotal != null && underTotal != null && Math.abs(overTotal - underTotal) < 0.001;
}
function bothBestWinPricesPositive(r) {
  return r && Number(r.best_over_odds) > 0 && Number(r.best_under_odds) > 0 && sameWinTotalForBestOverUnder(r);
}
function bestOverCell(r) {
  const mv = bestWinMovementForSide(r, 'over');
  const recent = bestWinRecentForSide(r, 'over');
  const open = mv ? openCurrentOddsLabel(mv.opening_over_odds, mv.current_over_odds, 'Best over odds: open → latest') : '<span class="market-move market-move-flat">Open —</span>';
  const latest = recent ? latestPullChip(recent.previous_over_odds, recent.current_over_odds, 'odds', 'Best over odds: previous pull → latest pull', recent.previous_snapshot_date) : '';
  const cls = bothBestWinPricesPositive(r) ? 'both-plus' : '';
  return `<div class="market-main">${compactBookThenOdds(r.best_over_odds, r.best_over_book, cls)}</div><div class="market-move-stack">${open}${latest}</div>`;
}

function bestUnderCell(r) {
  const mv = bestWinMovementForSide(r, 'under');
  const recent = bestWinRecentForSide(r, 'under');
  const open = mv ? openCurrentOddsLabel(mv.opening_under_odds, mv.current_under_odds, 'Best under odds: open → latest') : '<span class="market-move market-move-flat">Open —</span>';
  const latest = recent ? latestPullChip(recent.previous_under_odds, recent.current_under_odds, 'odds', 'Best under odds: previous pull → latest pull', recent.previous_snapshot_date) : '';
  const cls = bothBestWinPricesPositive(r) ? 'both-plus' : '';
  return `<div class="market-main">${compactBookThenOdds(r.best_under_odds, r.best_under_book, cls)}</div><div class="market-move-stack">${open}${latest}</div>`;
}

function bestTitleCell(r) {
  const mv = r.title_movement;
  const recent = titleRecentFor(r.team, r.conference, r.best_title_book);
  const open = mv ? openCurrentOddsLabel(mv.opening_american_odds, mv.current_american_odds, 'Best title odds: open → latest') : '<span class="market-move market-move-flat">Open —</span>';
  const latest = recent ? latestPullChip(recent.previous_american_odds, recent.current_american_odds, 'odds', 'Best title odds: previous pull → latest pull', recent.previous_snapshot_date) : '';
  return `<div class="market-main">${compactBookThenOdds(r.best_title_odds, r.best_title_book)}</div><div class="market-move-stack">${open}${latest}</div>`;
}

function titleMoveCell(r) {
  if (!r.title_movement) return '<span class="muted">—</span>';
  const oddsMove = movementArrow(r.title_movement.american_odds_move, 'odds', 'Title odds move');
  const implied = r.title_movement.implied_prob_move == null ? '' : `<div class="market-sub">Implied ${movementArrow(Number(r.title_movement.implied_prob_move || 0) * 100, 'line', 'Implied probability move')} pts</div>`;
  return `<div>${oddsMove}</div>${implied}`;
}

function marketBoardRows() {
  return DB.teams.map(t => {
    const m = marketForTeam(t.team);
    const winRows = rawWinRowsForTeam(t.team);
    const futRows = rawFuturesRowsForTeam(t.team);
    const projWins = Number(t.avg_total_wins);
    const projConfWins = Number(t.avg_conference_wins);
    const projTitle = Number(t.conference_title_pct);
    const marketTotalRaw = m ? marketWinLine(m) : null;
    const marketTotal = Number(marketTotalRaw);
    const winEdge = Number.isFinite(projWins) && Number.isFinite(marketTotal) ? projWins - marketTotal : null;
    const titleMarket = m && m.market_implied_title_prob != null ? Number(m.market_implied_title_prob) : null;
    const titleEdge = Number.isFinite(projTitle) && Number.isFinite(titleMarket) ? projTitle - titleMarket : null;
    return {
      team: t.team,
      conference: t.conference,
      rank: t.rank,
      combo: Number(t.combo),
      projected_wins: projWins,
      projected_conf_wins: projConfWins,
      projected_title_prob: projTitle,
      projected_title_odds: americanOddsNumberFromProb(projTitle),
      market_total: Number.isFinite(marketTotal) ? marketTotal : null,
      win_edge: winEdge,
      best_over_odds: m && m.best_over_odds,
      best_over_book: m && m.best_over_book,
      best_under_odds: m && m.best_under_odds,
      best_under_book: m && m.best_under_book,
      best_title_odds: m && m.best_title_odds,
      best_title_book: m && m.best_title_book,
      market_implied_title_prob: titleMarket,
      title_edge: titleEdge,
      books_available: m && m.books_available,
      has_market: !!m || winRows.length || futRows.length,
      win_movement: bestWinMovementForTeam(t.team, m),
      title_movement: bestTitleMovementForTeam(t.team, t.conference, m),
      m
    };
  });
}
function marketBoardValue(row, key) {
  const v = row[key];
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  return v == null ? '' : String(v);
}
function getMarketBoardFilters() {
  return {
    q: (localStorage.getItem('ncaaf_market_board_search') || '').trim().toLowerCase(),
    conf: localStorage.getItem('ncaaf_market_board_conf') || '',
    marketFilter: localStorage.getItem('ncaaf_market_board_data_filter') || 'all'
  };
}
function sortedMarketBoardRows() {
  const {q, conf, marketFilter} = getMarketBoardFilters();
  const key = marketBoardSortState.key;
  const dir = marketBoardSortState.dir === 'asc' ? 1 : -1;
  return marketBoardRows()
    .filter(r => !q || r.team.toLowerCase().includes(q) || String(r.conference || '').toLowerCase().includes(q))
    .filter(r => !conf || r.conference === conf)
    .filter(r => marketFilter === 'all' || (marketFilter === 'with_market' ? r.has_market : !r.has_market))
    .sort((a,b) => {
      const av = marketBoardValue(a,key), bv = marketBoardValue(b,key);
      const an = typeof av === 'number' ? av : Number(av);
      const bn = typeof bv === 'number' ? bv : Number(bv);
      if (Number.isFinite(an) || Number.isFinite(bn)) return ((Number.isFinite(an) ? an : -999999) - (Number.isFinite(bn) ? bn : -999999)) * dir;
      return String(av).localeCompare(String(bv)) * dir;
    });
}
function marketSortableTh(key, label, cls='') {
  const active = marketBoardSortState.key === key;
  const arrow = active ? (marketBoardSortState.dir === 'asc' ? ' ▲' : ' ▼') : '';
  const classAttr = cls ? ` class="${cls}"` : '';
  return `<th${classAttr} style="cursor:pointer" onclick="marketBoardSortState={key:'${key}',dir:${active && marketBoardSortState.dir === 'asc' ? "'desc'" : "'asc'"}}; route();">${label}${arrow}</th>`;
}
function compactBestOdds(odds, book) {
  if (odds == null || odds === '') return '—';
  return `${fmtOdds(odds)} <span class="small">${sportsbookLogo(book || '')}</span>`;
}
function compactBookThenOdds(odds, book, extraClass='') {
  if (odds == null || odds === '') return '—';
  const cls = extraClass ? `book-odds-inline ${extraClass}` : 'book-odds-inline';
  return `<span class="${cls}"><span class="book-odds-logo">${sportsbookLogo(book || '')}</span><strong>${fmtOdds(odds)}</strong></span>`;
}

function fmtMoveOdds(v) {
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  const n = Number(v);
  return n > 0 ? `+${Math.round(n)}` : `${Math.round(n)}`;
}

function fmtMoveWins(v) {
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  return Number(v).toFixed(1).replace(/\.0$/, '');
}

function openToCurrentChip(openVal, currentVal, kind='odds') {
  if (openVal == null || currentVal == null || openVal === '' || currentVal === '') return '';
  const same = Number(openVal) === Number(currentVal);
  if (same) return `<span class="market-open-current no-move">Open ${kind === 'wins' ? fmtMoveWins(openVal) : fmtMoveOdds(openVal)}</span>`;
  const cls = Number(currentVal) > Number(openVal) ? 'move-up' : 'move-down';
  const openText = kind === 'wins' ? fmtMoveWins(openVal) : fmtMoveOdds(openVal);
  const currentText = kind === 'wins' ? fmtMoveWins(currentVal) : fmtMoveOdds(currentVal);
  return `<span class="market-open-current ${cls}">${openText} → ${currentText}</span>`;
}

function compactWinBooksForBoard(team, m) {
  const by = bookRowsByKey(rawWinRowsForTeam(team));
  return MARKET_BOOKS.map(b => {
    const r = by[b.key];
    if (!r) return `<td class="market-win-cell muted"><span class="market-no-source">No line</span></td>`;
    const overBest = oddsEqual(r.over_odds, m && m.best_over_odds) && isBestBook(r.book, m && m.best_over_book);
    const underBest = oddsEqual(r.under_odds, m && m.best_under_odds) && isBestBook(r.book, m && m.best_under_book);
    const openBits = openWinSummary(team, r.book);
    const recentBits = winRecentSummary(team, r.book, 'all');
    const moves = (openBits || recentBits) ? `<div class="market-book-moves">${openBits}${recentBits}</div>` : '';
    return `<td class="market-win-cell"><div class="book-win-cell"><div class="book-win-total">${fmtWins(r.win_total)}</div><div class="book-win-prices"><div>O ${renderOddsCell(r.over_odds, overBest)}</div><div>U ${renderOddsCell(r.under_odds, underBest)}</div></div>${moves}</div></td>`;
  }).join('');
}

function compactTitleBooksForBoard(team, m) {
  const by = bookRowsByKey(rawFuturesRowsForTeam(team));
  return MARKET_BOOKS.map(b => {
    const r = by[b.key];
    if (!r) return `<td class="market-title-cell muted"><span class="market-no-source">No line</span></td>`;
    const titleBest = oddsEqual(r.american_odds, m && m.best_title_odds) && isBestBook(r.book, m && m.best_title_book);
    const open = openTitleSummary(team, r.conference, r.book);
    const recent = titleRecentSummary(team, r.conference, r.book);
    const moves = (open || recent) ? `<div class="market-book-moves">${open}${recent}</div>` : '';
    return `<td class="market-title-cell"><div>${renderOddsCell(r.american_odds, titleBest)}</div>${moves}</td>`;
  }).join('');
}

function marketAvailableBookKeys(m, type='wins') {
  const raw = String((m && m.books_available) || '').toLowerCase();
  return MARKET_BOOKS.filter(b => b.names.some(n => raw.includes(n))).map(b => b.key);
}
function marketDataAudit(rows, view) {
  let expected = 0;
  let missing = 0;
  const examples = [];
  rows.forEach(r => {
    const expectedBooks = marketAvailableBookKeys(r.m, view === 'titles' ? 'titles' : 'wins');
    if (!expectedBooks.length) return;
    const by = view === 'titles' ? bookRowsByKey(rawFuturesRowsForTeam(r.team)) : bookRowsByKey(rawWinRowsForTeam(r.team));
    expectedBooks.forEach(k => {
      expected += 1;
      if (!by[k]) {
        missing += 1;
        if (examples.length < 3) examples.push(`${r.team} ${bookLabelFromKey(k)}`);
      }
    });
  });
  if (!expected) return '';
  if (!missing) return `<div class="market-data-audit"><span class="market-audit-pill">Data check: all expected sportsbook fields are displaying for this view</span></div>`;
  return `<div class="market-data-audit"><span class="market-audit-pill warn">Data check: ${missing} expected sportsbook field${missing===1?'':'s'} still missing${examples.length ? ` — ${examples.join(', ')}` : ''}</span></div>`;
}


// Futures Market v7: show source coverage clearly. Blank sportsbook cells mean the raw export has no row for that team/book.
function marketDataAudit(rows, view) {
  let blankCells = 0;
  const examples = [];
  rows.forEach(r => {
    const by = view === 'titles' ? bookRowsByKey(rawFuturesRowsForTeam(r.team)) : bookRowsByKey(rawWinRowsForTeam(r.team));
    MARKET_BOOKS.forEach(b => {
      if (!by[b.key]) {
        blankCells += 1;
        if (examples.length < 5) examples.push(`${r.team} ${bookLabelFromKey(b.key)}`);
      }
    });
  });
  if (!blankCells) return `<div class="market-data-audit"><span class="market-audit-pill">Source coverage: all four sportsbook columns have raw rows for every visible team</span></div>`;
  return `<div class="market-data-audit"><span class="market-audit-pill info">Source coverage: ${blankCells} blank book cell${blankCells===1?'':'s'} in this view because the embedded raw export has no matching team/book row after aliases${examples.length ? ` — examples: ${examples.join(', ')}` : ''}</span></div>`;
}
function getMarketBoardView() {
  return localStorage.getItem('ncaaf_market_board_view') || 'wins';
}
function setMarketBoardView(view) {
  const allowed = ['wins','titles','moves','arbs'];
  localStorage.setItem('ncaaf_market_board_view', allowed.includes(view) ? view : 'wins');
  route();
}




function readMarketArbsData(){
  const el = document.getElementById('market-arbitrage-data');
  if (!el) return [];
  try { return JSON.parse(el.textContent || '[]'); }
  catch(e){ return []; }
}
function arbTypeClass(type){
  const t = String(type || '').toLowerCase();
  if (t.includes('arbitrage')) return 'arb';
  if (t.includes('no-vig')) return 'novig';
  return 'middle';
}
function arbTypeLabel(row){
  if (row.type === 'Middle') return row.quality || 'Middle';
  return row.type || '';
}

let marketArbSortState = {key:'edge_pct', dir:'desc'};

function setMarketArbSort(key){
  if (marketArbSortState.key === key) {
    marketArbSortState.dir = marketArbSortState.dir === 'asc' ? 'desc' : 'asc';
  } else {
    marketArbSortState.key = key;
    marketArbSortState.dir = key === 'team' || key === 'type' ? 'asc' : 'desc';
  }
  route();
}

function marketArbSortArrow(key){
  if (!marketArbSortState || marketArbSortState.key !== key) return '';
  return `<span class="sort-arrow">${marketArbSortState.dir === 'asc' ? '▲' : '▼'}</span>`;
}

function marketArbSortVal(row, key){
  if (key === 'type') return String(row.quality || row.type || '');
  if (key === 'team') return String(row.team || '');
  if (key === 'total') return Number(String(row.win_total || '').split('/')[0]) || -999;
  if (key === 'bet1') return String(row.side_1 || '');
  if (key === 'book1') return String(row.book_1 || '');
  if (key === 'odds1') return Number(String(row.odds_1 || '').replace('+','')) || -999;
  if (key === 'bet2') return String(row.side_2 || '');
  if (key === 'book2') return String(row.book_2 || '');
  if (key === 'odds2') return Number(String(row.odds_2 || '').replace('+','')) || -999;
  if (key === 'edge_pct') return Number(row.edge_pct || row.middle_score || -999);
  return '';
}

function sortMarketArbRows(rows){
  const key = marketArbSortState.key || 'edge_pct';
  const dir = marketArbSortState.dir === 'asc' ? 1 : -1;
  return [...rows].sort((a,b) => {
    const av = marketArbSortVal(a,key);
    const bv = marketArbSortVal(b,key);
    if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir;
    return String(av).localeCompare(String(bv)) * dir;
  });
}

function marketArbTh(key,label){
  return `<th class="sortable" onclick="setMarketArbSort('${key}')">${label}${marketArbSortArrow(key)}</th>`;
}

function renderMarketArbsBoard(){
  const confs = [...new Set(DB.teams.map(t => t.conference).filter(Boolean))].sort();
  const rowsAll = readMarketArbsData();

  const arbs = rowsAll.filter(r => r.type === 'Arbitrage');
  const novig = rowsAll.filter(r => r.type === 'No-vig / Break-even');
  const strongMiddles = rowsAll.filter(r => r.quality === 'Strong middle');
  const playableMiddles = rowsAll.filter(r => r.quality === 'Playable middle');

  let displayRows = rowsAll.filter(r =>
    r.type === 'Arbitrage' ||
    r.type === 'No-vig / Break-even' ||
    r.quality === 'Strong middle' ||
    r.quality === 'Playable middle'
  );
  displayRows = sortMarketArbRows(displayRows);

  return `
    <div class="page-title">Futures Market</div>
    <div class="page-sub">All-team board, latest market moves, and stale-price scanner for win-total arbitrage / middle opportunities.</div>

    <div class="mobile-actions">
      <a class="pill" href="#rankings">Rankings</a>
      <a class="pill" href="#conferences">Conferences</a>
      <a class="pill" href="#schedule">Schedule</a>
    </div>

    <div class="card" style="margin-top:16px">
      <div class="section-title">Filters</div>
      <div class="filter-grid market-filter-grid">
        <label class="market-filter-control"><span>Conference</span><select id="marketBoardConf">
          <option value="">All conferences</option>
          ${confs.map(c=>`<option value="${escapeHtml(c)}" ${getMarketBoardFilters().conf===c?'selected':''}>${escapeHtml(c)}</option>`).join('')}
        </select></label>
        <label class="market-filter-control"><span>Search</span><input id="marketBoardSearch" placeholder="Filter team or conference" value="${escapeHtml(localStorage.getItem('ncaaf_market_board_search') || '')}" /></label>
        <label class="market-filter-control"><span>Market coverage</span><select id="marketBoardDataFilter">
          <option value="all" ${getMarketBoardFilters().marketFilter==='all'?'selected':''}>All teams</option>
          <option value="with_market" ${getMarketBoardFilters().marketFilter==='with_market'?'selected':''}>Only teams with market data</option>
          <option value="without_market" ${getMarketBoardFilters().marketFilter==='without_market'?'selected':''}>Teams missing market data</option>
        </select></label>
      </div>
      <div class="small muted" style="margin-top:10px">Arbitrage rows are same-total opposite-side pairs where implied probabilities sum below 100%. Middles are over-lower / under-higher win-total gaps.</div>
    </div>

    <div class="card desktop-rankings market-board-card market-arb-board-card" style="margin-top:16px">
      <div class="section-title">All-Team Futures Market Board</div>
      <div class="market-view-toggle" role="tablist" aria-label="Futures market view">
        <button type="button" class="win-view" onclick="setMarketBoardView('wins')">Win totals</button>
        <button type="button" class="title-view" onclick="setMarketBoardView('titles')">Conference title odds</button>
        <button type="button" class="market-moves-view-btn" onclick="setMarketBoardView('moves')">Latest market moves</button>
        <button type="button" class="arb-view active" onclick="setMarketBoardView('arbs')">Arbs / Middles</button>
      </div>

      <div class="market-arb-head">
        <div>
          <div class="market-arb-title">Arbs / Middles</div>
          <div class="market-arb-sub">Showing true arbs, no-vig pairs, and strong/playable middles. Weak middles are kept in CSV but hidden here by default.</div>
        </div>
        <div class="market-arb-pills">
          <span class="market-arb-pill">Arbs: <b>${arbs.length}</b></span>
          <span class="market-arb-pill">No-vig: <b>${novig.length}</b></span>
          <span class="market-arb-pill">Strong middles: <b>${strongMiddles.length}</b></span>
          <span class="market-arb-pill">Playable middles: <b>${playableMiddles.length}</b></span>
          <span class="market-arb-pill">Loaded: <b>${rowsAll.length}</b></span>
        </div>
      </div>

      ${displayRows.length ? `
      <div class="market-arb-table-wrap">
        <table class="market-arb-table">
          <thead>
            <tr>
              ${marketArbTh('type','Type')}
              ${marketArbTh('team','Team')}
              ${marketArbTh('total','Total')}
              ${marketArbTh('bet1','Bet 1')}
              ${marketArbTh('book1','Book 1')}
              ${marketArbTh('odds1','Odds 1')}
              ${marketArbTh('bet2','Bet 2')}
              ${marketArbTh('book2','Book 2')}
              ${marketArbTh('odds2','Odds 2')}
              ${marketArbTh('edge_pct','Edge / Score')}
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            ${displayRows.map(r => `
              <tr>
                <td><span class="market-arb-type ${arbTypeClass(r.type)}">${escapeHtml(arbTypeLabel(r))}</span></td>
                <td>${typeof linkTeam === 'function' ? linkTeam(r.team) : escapeHtml(r.team || '')}</td>
                <td>${escapeHtml(String(r.win_total || ''))}</td>
                <td>${escapeHtml(r.side_1 || '')}</td>
                <td>${escapeHtml(r.book_1 || '')}</td>
                <td><b>${escapeHtml(String(r.odds_1 || ''))}</b></td>
                <td>${escapeHtml(r.side_2 || '')}</td>
                <td>${escapeHtml(r.book_2 || '')}</td>
                <td><b>${escapeHtml(String(r.odds_2 || ''))}</b></td>
                <td>${r.edge_pct !== '' && r.edge_pct != null ? `<span class="market-arb-edge">${escapeHtml(String(r.edge_pct))}%</span>` : escapeHtml(String(r.middle_score || ''))}</td>
                <td class="small">${escapeHtml(r.notes || '')}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>` : `<div class="market-arb-empty">No arbitrage or playable middle opportunities found.</div>`}
    </div>
  `;
}


function renderMarketMovesBoard(){
  const confs = [...new Set(DB.teams.map(t => t.conference).filter(Boolean))].sort();
  const view = 'moves';

  function readRows(){
    const el = document.getElementById('daily-market-moves-data');
    if (!el) return [];
    try { return JSON.parse(el.textContent || '[]'); }
    catch(e){ return []; }
  }

  function moveDate(row){
    return row.move_date || row.snapshot_latest || '';
  }

  function moveImpactClass(v){
    const n = Number(v);
    if (!Number.isFinite(n)) return '';
    return n > 0 ? 'imp-pos' : n < 0 ? 'imp-neg' : '';
  }

  function dateRange(rows){
    const dates = rows.map(moveDate).filter(Boolean).sort();
    if (!dates.length) return '';
    const first = dates[0];
    const last = dates[dates.length - 1];
    return first === last ? first : `${first} to ${last}`;
  }

  const injectedRows = injectedDailyMarketMovesRows();
  const allRows = injectedRows.length ? injectedRows : readRows();
  const rows = [...allRows].sort((a,b) => {
    const da = String(moveDate(a));
    const db = String(moveDate(b));
    if (da !== db) return db.localeCompare(da);
    const ia = Math.abs(Number(a.implied_prob_change_pct || 0));
    const ib = Math.abs(Number(b.implied_prob_change_pct || 0));
    return ib - ia;
  });

  const winRows = rows.filter(r => String(r.market || '').toLowerCase().includes('win'));
  const confRows = rows.filter(r => String(r.market || '').toLowerCase().includes('conference'));
  const range = dateRange(rows);

  const body = rows.map(r => {
    const imp = r.implied_prob_change_pct;
    const impNum = Number(imp);
    const impText = (imp !== '' && imp != null && Number.isFinite(impNum))
      ? ` <span class="${moveImpactClass(imp)}">${impNum > 0 ? '+' : ''}${impNum}% implied</span>`
      : '';
    const prev = r.previous == null ? '' : String(r.previous);
    const latest = r.latest == null ? '' : String(r.latest);

    return `
      <div class="market-move-row">
        <div class="market-move-date">${escapeHtml(moveDate(r))}</div>
        <div class="market-move-kind">${escapeHtml(String(r.market || ''))}</div>
        <div class="market-move-team">${typeof linkTeam === 'function' ? linkTeam(r.team) : escapeHtml(String(r.team || ''))}</div>
        <div class="market-move-book">${escapeHtml(String(r.book || ''))}</div>
        <div class="market-move-bet">${escapeHtml(String(r.field || ''))}</div>
        <div class="market-move-change">${escapeHtml(prev)} → ${escapeHtml(latest)}${impText}</div>
      </div>`;
  }).join('');

  const movesHtml = `<div class="market-moves-panel active">
    <div class="market-moves-sticky">
      <div class="market-moves-head">
        <div>
          <div class="market-moves-head-title">Latest Market Moves</div>
          <div class="market-moves-head-sub">Last 7 days of current movement data${range ? ` · ${escapeHtml(range)}` : ''}</div>
        </div>
        <div class="market-moves-pill-row">
          <span class="market-moves-pill">7-day moves: <b>${rows.length}</b></span>
          <span class="market-moves-pill">Win totals: <b>${winRows.length}</b></span>
          <span class="market-moves-pill">Conf futures: <b>${confRows.length}</b></span>
          <span class="market-moves-pill">Loaded rows: <b>${allRows.length}</b></span>
        </div>
      </div>
      <div class="market-move-header">
        <button>Date</button>
        <button>Market</button>
        <button>Team</button>
        <button>Book</button>
        <button>Bet</button>
        <button>Move</button>
      </div>
    </div>
    ${rows.length ? `<div class="market-moves-list">${body}</div>` : `<div class="market-move-empty">No recent market moves loaded.</div>`}
  </div>`;

  return `
    <div class="page-title">Futures Market</div>
    <div class="page-sub">All-team board comparing projected wins, projected conference wins, and projected conference title probability against imported win-total and conference-futures prices. Movement labels compare first captured price to latest captured price.</div>

    <div class="mobile-actions">
      <a class="pill" href="#rankings">Rankings</a>
      <a class="pill" href="#conferences">Conferences</a>
      <a class="pill" href="#schedule">Schedule</a>
    </div>

    <div class="card" style="margin-top:16px">
      <div class="section-title">Filters</div>
      <div class="filter-grid market-filter-grid">
        <label class="market-filter-control"><span>Conference</span><select id="marketBoardConf">
          <option value="">All conferences</option>
          ${confs.map(c=>`<option value="${escapeHtml(c)}" ${getMarketBoardFilters().conf===c?'selected':''}>${escapeHtml(c)}</option>`).join('')}
        </select></label>
        <label class="market-filter-control"><span>Search</span><input id="marketBoardSearch" placeholder="Filter team or conference" value="${escapeHtml(localStorage.getItem('ncaaf_market_board_search') || '')}" /></label>
        <label class="market-filter-control"><span>Market coverage</span><select id="marketBoardDataFilter">
          <option value="all" ${getMarketBoardFilters().marketFilter==='all'?'selected':''}>All teams</option>
          <option value="with_market" ${getMarketBoardFilters().marketFilter==='with_market'?'selected':''}>Only teams with market data</option>
          <option value="without_market" ${getMarketBoardFilters().marketFilter==='without_market'?'selected':''}>Teams missing market data</option>
        </select></label>
      </div>
      <div class="small muted" style="margin-top:10px">Latest market moves show true daily movement dates from the last 7 days.</div>
    </div>

    <div class="card desktop-rankings market-board-card" style="margin-top:16px">
      <div class="section-title">All-Team Futures Market Board</div>
      <div class="market-view-toggle" role="tablist" aria-label="Futures market view">
        <button type="button" class="win-view" onclick="setMarketBoardView('wins')">Win totals</button>
        <button type="button" class="title-view" onclick="setMarketBoardView('titles')">Conference title odds</button>
        <button type="button" class="market-moves-view-btn active" onclick="setMarketBoardView('moves')">Latest market moves</button>
        <button type="button" class="arb-view" onclick="setMarketBoardView('arbs')">Arbs / Middles</button>
      </div>
      ${movesHtml}
    </div>
  `;
}

function injectedDailyMarketMovesRows() {
  const el = document.getElementById('daily-market-moves-data');
  if (!el) return [];
  try {
    const rows = JSON.parse(el.textContent || '[]');
    return Array.isArray(rows) ? rows : [];
  } catch (e) {
    console.warn('Could not parse daily-market-moves-data', e);
    return [];
  }
}

function renderMarketBoard() {
  const rows = sortedMarketBoardRows();
  const confs = [...new Set(DB.teams.map(t => t.conference).filter(Boolean))].sort();
  const view = getMarketBoardView();
  if (view === 'moves') return renderMarketMovesBoard();
  if (view === 'arbs') return renderMarketArbsBoard();
  const isTitles = view === 'titles';
  const tableClass = isTitles ? 'futures-board-table title-only' : 'futures-board-table win-only';
  const groupTitle = isTitles ? 'Conference Futures' : 'Win Totals';
  const groupClass = isTitles ? 'market-title-head' : 'market-win-head';
  const headerCols = isTitles ? `
            ${marketSortableTh('projected_title_odds','Proj Title Odds','market-title-cell')}
            ${marketSortableTh('projected_title_prob','Proj Title %','market-title-cell')}
            ${marketSortableTh('market_implied_title_prob','Consensus Market Title %','market-title-cell')}
            ${marketSortableTh('title_edge','Title Edge','market-title-cell')}
            <th class="market-title-cell">Best Title Odds<div class="market-header-open-date">Line movement</div></th>
            ${MARKET_BOOKS.map(b=>`<th class="market-title-cell">${sportsbookHeaderLogo(b.label,'Title')}</th>`).join('')}` : `
            ${marketSortableTh('projected_wins','Proj Wins','market-win-cell')}
            ${marketSortableTh('market_total','Consensus Market Wins','market-win-cell')}
            ${marketSortableTh('win_edge','Win Edge','market-win-cell')}
            <th class="market-win-cell">${bestWinHeader("BEST OVER")}</th>
            <th class="market-win-cell">${bestWinHeader("BEST UNDER")}</th>
            ${MARKET_BOOKS.map(b=>`<th class="market-win-cell">${sportsbookHeaderLogo(b.label,'Win Total')}</th>`).join('')}`;
  const bodyRows = rows.map(r => {
    const marketCols = isTitles ? `
              <td class="market-title-cell">${fmtOdds(r.projected_title_odds)}</td>
              <td class="market-title-cell">${fmtMarketPct(r.projected_title_prob)}</td>
              <td class="market-title-cell">${fmtMarketPct(r.market_implied_title_prob)}</td>
              <td class="market-title-cell ${r.title_edge == null ? '' : (r.title_edge > 0 ? 'pos' : r.title_edge < 0 ? 'neg' : '')}">${r.title_edge == null ? '—' : fmtMarketPct(r.title_edge)}</td>
              <td class="market-title-cell">${bestTitleCell(r)}</td>
              ${compactTitleBooksForBoard(r.team, r.m)}` : `
              <td class="market-win-cell">${fmtWins(r.projected_wins)}</td>
              <td class="market-win-cell">${marketTotalCell(r)}</td>
              <td class="market-win-cell ${fmtSignedClass(r.win_edge)}">${r.win_edge == null ? '—' : fmtSigned(r.win_edge)}</td>
              <td class="market-win-cell">${bestOverCell(r)}</td>
              <td class="market-win-cell">${bestUnderCell(r)}</td>
              ${compactWinBooksForBoard(r.team, r.m)}`;
    return `
            <tr>
              <td class="market-sticky-cell">${r.rank}</td>
              <td class="market-sticky-cell">${linkTeam(r.team)}</td>
              <td class="market-sticky-cell">${linkConf(r.conference)}</td>
              ${marketCols}
            </tr>`;
  }).join('');
  return `
    <div class="page-title">Futures Market</div>
    <div class="page-sub">All-team board comparing projected wins, projected conference wins, and projected conference title probability against imported win-total and conference-futures prices. Movement labels compare first captured price to latest captured price.</div>
    
    <div class="mobile-actions">
      <a class="pill" href="#rankings">Rankings</a>
      <a class="pill" href="#conferences">Conferences</a>
      <a class="pill" href="#schedule">Schedule</a>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="section-title">Filters</div>
      <div class="filter-grid market-filter-grid">
        <label class="market-filter-control"><span>Conference</span><select id="marketBoardConf">
          <option value="">All conferences</option>
          ${confs.map(c=>`<option value="${escapeHtml(c)}" ${getMarketBoardFilters().conf===c?'selected':''}>${escapeHtml(c)}</option>`).join('')}
        </select></label>
        <label class="market-filter-control"><span>Search</span><input id="marketBoardSearch" placeholder="Filter team or conference" value="${escapeHtml(localStorage.getItem('ncaaf_market_board_search') || '')}" /></label>
        <label class="market-filter-control"><span>Market coverage</span><select id="marketBoardDataFilter">
          <option value="all" ${getMarketBoardFilters().marketFilter==='all'?'selected':''}>All teams</option>
          <option value="with_market" ${getMarketBoardFilters().marketFilter==='with_market'?'selected':''}>Only teams with market data</option>
          <option value="without_market" ${getMarketBoardFilters().marketFilter==='without_market'?'selected':''}>Teams missing market data</option>
        </select></label>
      </div>
      <div class="small muted" style="margin-top:10px">Rows shown: ${rows.length}. Market fields come from market_futures_export.xlsx. Projection fields come from the embedded team data.</div>
      ${marketDataAudit(rows, view)}
    </div>
    <div class="card desktop-rankings market-board-card" style="margin-top:16px">
      <div class="section-title">All-Team Futures Market Board</div>
      <div class="market-view-toggle" role="tablist" aria-label="Futures market view">
        <button type="button" class="win-view ${view === 'wins' ? 'active' : ''}" onclick="setMarketBoardView('wins')">Win totals</button>
        <button type="button" class="title-view ${view === 'titles' ? 'active' : ''}" onclick="setMarketBoardView('titles')">Conference title odds</button>
        <button type="button" class="market-moves-view-btn ${view === 'moves' ? 'active' : ''}" onclick="setMarketBoardView('moves')">Latest market moves</button>
        <button type="button" class="arb-view ${view === 'arbs' ? 'active' : ''}" onclick="setMarketBoardView('arbs')">Arbs / Middles</button>
      </div>
      <div class="market-table-scroll">
      <table class="${tableClass}">
        <thead>
          <tr class="market-group-row">
            <th colspan="3" class="market-sticky-group">Team</th>
            <th colspan="9" class="${groupClass}">${groupTitle}</th>
          </tr>
          <tr>
            ${marketSortableTh('rank','Rank','market-sticky-cell')}
            ${marketSortableTh('team','Team','market-sticky-cell')}
            ${marketSortableTh('conference','Conf','market-sticky-cell')}
            ${headerCols}
          </tr>
        </thead>
        <tbody>${bodyRows}</tbody>
      </table>
      </div>
    </div>
  `;
}
function mountMarketBoardControls() {
  const conf = byId('marketBoardConf');
  const search = byId('marketBoardSearch');
  const dataFilter = byId('marketBoardDataFilter');
  if (!conf || !search || !dataFilter) return;

  conf.addEventListener('change', () => {
    localStorage.setItem('ncaaf_market_board_conf', conf.value);
    route();
  });

  dataFilter.addEventListener('change', () => {
    localStorage.setItem('ncaaf_market_board_data_filter', dataFilter.value);
    route();
  });

  search.addEventListener('input', () => {
    localStorage.setItem('ncaaf_market_board_search', search.value);
    const cursor = search.selectionStart || search.value.length;
    byId('app').innerHTML = renderMarketBoard();
    mountMarketBoardControls();
    const s = byId('marketBoardSearch');
    if (s) {
      s.focus();
      try { s.setSelectionRange(cursor, cursor); } catch(e) {}
    }
  });
}


function rankToneClass(rank) {
  const r = Number(rank);
  if (!Number.isFinite(r)) return 'rank-na';
  if (r <= 25) return 'rank-elite';
  if (r <= 75) return 'rank-good';
  if (r <= 105) return 'rank-mid';
  return 'rank-bad';
}
function rankBadge(rank) {
  if (rank == null || rank === '' || rank === '—') return '<span class="rank-badge rank-na">—</span>';
  return `<span class="rank-badge ${rankToneClass(rank)}">#${rank}</span>`;
}

function ratingTrendTone(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return '';
  if (n > 0.05) return 'pos';
  if (n < -0.05) return 'neg';
  return 'muted';
}
function fmtRatingTrend(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return '—';
  return (n > 0 ? '+' : '') + n.toFixed(1);
}
function fmtRankTrend(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return '—';
  if (n === 0) return 'No rank change';
  return n > 0 ? `Up ${Math.abs(Math.round(n))}` : `Down ${Math.abs(Math.round(n))}`;
}
function ratingTrendBlock(teamName) {
  const tr = RATING_TRENDS[String(teamName || '')];
  if (!tr) return '';

  const trendTone = ratingTrendTone(tr.rating_trend);
  const rankTone = ratingTrendTone(tr.rank_trend);

  const blend2025 = tr.rating_2025_eoy == null
    ? '—'
    : `${Number(tr.rating_2025_eoy).toFixed(1)} <span class="muted">(#${tr.rank_2025_eoy || '—'})</span>`;

  const current2026 = tr.rating_2026_current == null
    ? '—'
    : `${Number(tr.rating_2026_current).toFixed(1)} <span class="muted">(#${tr.rank_2026_current || '—'})</span>`;

  const sourceNote = tr.source_count_2025 == null
    ? 'No 2025 FBS source blend'
    : `${tr.source_count_2025}/5 sources`;

  return `<div class="rating-trend-box">
    <div class="rating-trend-title">Rating Trend</div>
    <div class="rating-trend-grid">
      <div>
        <div class="label">2026 Current</div>
        <div class="value">${current2026}</div>
      </div>
      <div>
        <div class="label">2025 EOY Blend</div>
        <div class="value">${blend2025}</div>
      </div>
      <div>
        <div class="label">Rating Change</div>
        <div class="value ${trendTone}">${fmtRatingTrend(tr.rating_trend)}</div>
      </div>
      <div>
        <div class="label">Rank Change</div>
        <div class="value ${rankTone}">${fmtRankTrend(tr.rank_trend)}</div>
      </div>
    </div>
    <div class="small muted rating-trend-note">2025 EOY is five-system blend where available. 2026 current is latest official/default Power Rating. ${sourceNote}.</div>
  </div>`;
}

function ratingRow(label, value, rank, suffix='') {
  const v = value == null || value === '' ? '—' : value;
  return `<tr><td class="muted">${label}</td><td class="rating-value">${v}${suffix}</td><td>${rankBadge(rank)}</td></tr>`;
}
function marketMetric(label, value, cls='') {
  return `<div class="market-metric"><div class="label">${label}</div><div class="value ${cls}">${value}</div></div>`;
}

function coachForTeam(teamName) {
  return coachBettingByTeam[String(teamName || '').toLowerCase()] || null;
}
function coach1hForTeam(teamName) {
  return coach1hBettingByTeam[String(teamName || '').toLowerCase()] || null;
}
function coach2hForTeam(teamName) {
  return coach2hBettingByTeam[String(teamName || '').toLowerCase()] || null;
}
function coachTrendMiniRow(label, r) {
  if (!r) {
    return `<tr><td class="muted nowrap">${label}</td><td colspan="6">No data</td></tr>`;
  }
  return `<tr>
    <td class="muted nowrap">${label}</td>
    <td class="record-cell">${r.ats_record || '—'} <span class="small">#${r.ats_rank || '—'}</span></td>
    <td>${fmtPct(r.ats_pct)}</td>
    <td class="${fmtSignedClass(r.avg_ats_margin)}">${fmtSigned(r.avg_ats_margin)}</td>
    <td class="record-cell">${r.ou_record || '—'}</td>
    <td>${fmtPct(r.over_pct)}</td>
    <td class="${fmtSignedClass(r.avg_total_margin)}">${fmtSigned(r.avg_total_margin)}</td>
  </tr>`;
}
function renderTeamCoachCard(teamName) {
  const c = coachForTeam(teamName);
  const h1 = coach1hForTeam(teamName);
  const h2 = coach2hForTeam(teamName);
  const base = c || h1 || h2;
  if (!base) {
    return `<div class="card coach-trends-card"><div class="section-title">Head Coach Betting Trends</div><div class="small">No coach betting summary is currently mapped for this team.</div></div>`;
  }
  return `<div class="card coach-trends-card"><div class="section-title">Head Coach Betting Trends</div>
    <table class="compact-table coach-trend-table"><tbody>
      <tr><td class="muted">Head Coach</td><td colspan="6">${base.head_coach}</td></tr>
      <tr><td class="muted">Tracked Teams</td><td colspan="6">${base.teams_tracked || base.team}</td></tr>
      <tr><td class="muted nowrap">Period</td><td>ATS</td><td>ATS %</td><td>ATS +/-</td><td>O/U</td><td>Over %</td><td>Total +/-</td></tr>
      ${coachTrendMiniRow('Full Game', c)}
      ${coachTrendMiniRow('1st Half', h1)}
      ${coachTrendMiniRow('2nd Half', h2)}
    </tbody></table>
    <div class="small" style="margin-top:10px">Full-game metrics use tracked team-season betting trends through 2025. 1H/2H metrics use refreshed SportsGameOdds history through 2026-01-20.</div>
  </div>`;
}
function linkConf(name) {
  const c = DB.conferences.find(x=>x.conference===name);
  return c ? `<a class="linkish" href="javascript:void(0)" onclick="location.hash='#conference/${c.slug}'; route(); return false;">${name}</a>` : name;
}
function gamesForTeam(team) {
  return DB.games.filter(g => g.away_team===team || g.home_team===team);
}
function scheduleSortValue(g, key) {
  const st = gameState(g);
  const res = gameResultParts(g);
  const ms = marketSpread(g), mt = marketTotal(g);
  const h1s = market1HSpread(g), h1t = market1HTotal(g);
  const spreadEdge = ms == null || ms === '' ? null : Number(g.projected_margin_home) + Number(ms);
  const totalEdge = mt == null || mt === '' ? null : Number(g.projected_total) - Number(mt);
  if (key === 'week') return Number(g.week);
  if (key === 'date') return g.date || '';
  if (key === 'away') return (g.away_team || '').toLowerCase();
  if (key === 'home') return (g.home_team || '').toLowerCase();
  if (key === 'conf') return (g.home_conference || '').toLowerCase();
  if (key === 'neutral') return g.neutral_site ? 1 : 0;
  if (key === 'proj_spread') return Number(g.projected_margin_home);
  if (key === 'market_spread') return ms == null || ms === '' ? null : Number(ms);
  if (key === 'spread_edge') return spreadEdge;
  if (key === 'proj_total') return Number(g.projected_total);
  if (key === 'market_total') return mt == null || mt === '' ? null : Number(mt);
  if (key === 'total_edge') return totalEdge;
    if (key === 'ats_ev') {
      const m = bestAtsMarket(g), e = m.edge, p = atsModelProb(e);
      return e == null || p == null ? null : evFromProbAndOdds(p, defaultPrice(m.price)) * 100;
    }
    if (key === 'ats_betscore') {
      const m = bestAtsMarket(g), e = m.edge, p = atsModelProb(e);
      if (e == null || p == null) return null;
      return betScore(e, evFromProbAndOdds(p, defaultPrice(m.price)) * 100, g.market_books_count);
    }
    if (key === 'total_ev') {
      const m = bestTotalMarket(g), e = m.edge, p = totalModelProb(e);
      return e == null || p == null ? null : evFromProbAndOdds(p, defaultPrice(m.price)) * 100;
    }
    if (key === 'total_betscore') {
      const m = bestTotalMarket(g), e = m.edge, p = totalModelProb(e);
      if (e == null || p == null) return null;
      return betScore(e, evFromProbAndOdds(p, defaultPrice(m.price)) * 100, g.market_books_count);
    }
  if (key === 'one_h_spread') return h1s == null || h1s === '' ? null : Number(h1s);
  if (key === 'one_h_total') return h1t == null || h1t === '' ? null : Number(h1t);
  if (key === 'home_win') return Number(g.win_prob_home);
  if (key === 'status') return st.status === 'final' ? 1 : 0;
  if (key === 'score') return gameScoreText(g) === '—' ? null : Number(st.home_score) + Number(st.away_score) / 1000;
  if (key === 'winner') return (res.winner || '').toLowerCase();
  if (key === 'margin') return res.margin === '—' ? null : Number(res.margin);
  if (key === 'total_pts') return res.total === '—' ? null : Number(res.total);
  if (key === 'cfbd_id') return st.cfbd_game_id || g.cfbd_game_id || '';
  return g[key];
}
function sortScheduleGames(games) {
  const {key, dir} = scheduleSortState;
  const mult = dir === 'asc' ? 1 : -1;
  return [...games].sort((a,b) => {
    let av = scheduleSortValue(a, key), bv = scheduleSortValue(b, key);
    const aMissing = av === undefined || av === null || av === '' || Number.isNaN(av);
    const bMissing = bv === undefined || bv === null || bv === '' || Number.isNaN(bv);
    if (aMissing && bMissing) return String(a.date || '').localeCompare(String(b.date || '')) || (Number(a.week)-Number(b.week)) || String(a.away_team).localeCompare(String(b.away_team));
    if (aMissing) return 1;
    if (bMissing) return -1;
    if (typeof av === 'string' || typeof bv === 'string') {
      const cmp = String(av).localeCompare(String(bv));
      return cmp !== 0 ? cmp * mult : String(a.date || '').localeCompare(String(b.date || '')) || Number(a.week)-Number(b.week);
    }
    if (av === bv) return String(a.date || '').localeCompare(String(b.date || '')) || Number(a.week)-Number(b.week);
    return (av - bv) * mult;
  });
}
function scheduleSortArrow(key) {
  return scheduleSortState.key === key ? `<span class="sort-arrow">${scheduleSortState.dir === 'asc' ? '▲' : '▼'}</span>` : '';
}
function scheduleTh(key, label) {
  return `<th class="sortable" onclick="setScheduleSort('${key}')">${label}${scheduleSortArrow(key)}</th>`;
}
function setScheduleSort(key) {
  if (scheduleSortState.key === key) scheduleSortState.dir = scheduleSortState.dir === 'asc' ? 'desc' : 'asc';
  else {
    scheduleSortState.key = key;
    scheduleSortState.dir = ['week','date','away','home','conf','cfbd_id'].includes(key) ? 'asc' : 'desc';
  }
  drawScheduleTableFromCurrentFilters();
}

function ratingLabWeightsAreDefault() {
  const w = getRatingLabWeights();
  return ratingLabSystems().every(s => Math.round(Number(w[s] || 0) * 100) === Math.round(Number(DEFAULT_RATING_WEIGHTS[s] || 0) * 100));
}
function ratingLabDefaultWeightSummaryText() {
  return ratingLabSystems()
    .map(s => ({label: ratingLabLabel(s), pct: Math.round(Number(DEFAULT_RATING_WEIGHTS[s] || 0) * 100)}))
    .map(x => `${x.label} ${x.pct}%`)
    .join(', ');
}

function ratingLabWeightSummaryText() {
  const w = getRatingLabWeights();
  const parts = ratingLabSystems()
    .map(s => ({s, pct: Math.round(Number(w[s] || 0) * 100)}))
    .filter(x => x.pct > 0)
    .map(x => `${ratingLabLabel(x.s)} ${x.pct}%`);
  return parts.length ? parts.join(' / ') : 'No active weights';
}
function scheduleSpreadTh(key, label) {
  const note = ratingLabWeightsAreDefault() ? 'Default weights' : `Lab: ${ratingLabWeightSummaryText()}`;
  return `<th class="sortable schedule-spread-th" onclick="setScheduleSort('${key}')">
    <div>${label}${scheduleSortArrow(key)}</div>
    <div class="schedule-spread-weight-note">${note}</div>
  </th>`;
}
function scheduleSpreadCell(g) {
  const useLab = !ratingLabWeightsAreDefault();
  const txt = useLab ? labSpreadText(g) : spreadText(g);
  return `<div class="schedule-spread-cell"><div class="line-main">${txt}</div></div>`;
}



// Matchup engine helpers. Data is embedded by scripts/cfbd/inject_matchups_into_index.py.
function matchupNormName(name){ return String(name || '').toLowerCase().replace(/&/g,'and').replace(/[^a-z0-9]+/g,' ').trim().replace(/\s+/g,' '); }
function matchupGameId(g){ return String(g.cfbd_game_id || g.game_id || `${g.season || 2026}-${g.week}-${g.away_team}-${g.home_team}-${g.date}`); }
function matchupDomIdFromGameId(id){
  return 'matchup-row-' + String(id || '').replace(/[^A-Za-z0-9_-]/g, '_');
}
function matchupDomId(g){
  return matchupDomIdFromGameId(matchupGameId(g));
}
function matchupRows(){ return Array.isArray(DB.game_matchup_edges) ? DB.game_matchup_edges : []; }

const matchupEdgeIndex = (() => {
  const out = {};
  matchupRows().forEach(r => {
    const gid = String(r.game_id || '');
    const week = String(r.week || '');
    const team = matchupNormName(r.team);
    const opp = matchupNormName(r.opponent);
    if (gid) out[`gid|${gid}|${team}|${opp}`] = r;
    if (week) out[`week|${week}|${team}|${opp}`] = r;
  });
  return out;
})();

function matchupForGameTeam(g, team){
  const gid = matchupGameId(g);
  const tn = matchupNormName(team);
  const opp = team === g.home_team ? g.away_team : g.home_team;
  const on = matchupNormName(opp);
  const week = String(g.week);

  return matchupEdgeIndex[`gid|${gid}|${tn}|${on}`]
      || matchupEdgeIndex[`week|${week}|${tn}|${on}`]
      || null;
}
function matchupSigned(v){ if (v == null || v === '' || !isFinite(Number(v))) return '—'; const n = Number(v); return (n > 0 ? '+' : '') + n.toFixed(1); }
function matchupClass(v){ if (v == null || v === '' || !isFinite(Number(v)) || Math.abs(Number(v)) < .05) return ''; return Number(v) > 0 ? 'pos' : 'neg'; }
function matchupMetric(label, value, sub=''){
  return `<div class="matchup-card"><div class="matchup-label">${label}</div><div class="matchup-value ${matchupClass(value)}">${matchupSigned(value)}</div>${sub ? `<div class="matchup-sub">${sub}</div>` : ''}</div>`;
}
function setupClamp(n, lo, hi){
  n = Number(n || 0);
  return Math.max(lo, Math.min(hi, n));
}
function setupGrade(score){
  if (score >= 75) return {grade:'A', checks:'✓✓✓', label:'Strong setup', cls:'grade-a'};
  if (score >= 55) return {grade:'B', checks:'✓✓', label:'Good setup', cls:'grade-b'};
  if (score >= 35) return {grade:'C', checks:'✓', label:'Watchlist', cls:'grade-c'};
  return {grade:'Even', checks:'', label:'No edge', cls:'grade-even'};
}
function setupRankPoints(rank){
  if (rank == null || rank === '' || !isFinite(Number(rank))) return 0;
  const r = Number(rank);
  if (r <= 15) return 10;
  if (r <= 35) return 7;
  if (r <= 60) return 4;
  if (r >= 115) return -8;
  if (r >= 95) return -5;
  if (r >= 80) return -2;
  return 0;
}
function setupCoachRankEdgePoints(teamRank, oppRank, period){
  if (teamRank == null || oppRank == null || !isFinite(Number(teamRank)) || !isFinite(Number(oppRank))) return 0;

  const tr = Number(teamRank);
  const or = Number(oppRank);
  const diff = or - tr; // positive means team has better/lower rank
  const isFG = period === 'FG';

  let pts = 0;

  // Strong rank-tier advantages.
  if (tr <= 15 && or > 35) pts = isFG ? 8 : 5;
  else if (tr <= 25 && or > 50) pts = isFG ? 7 : 4.5;
  else if (tr <= 35 && or > 70) pts = isFG ? 6 : 4;
  else if (tr <= 50 && or > 90) pts = isFG ? 4.5 : 3;

  // Smaller visible edges, like Oregon #25 1H vs UCLA #72.
  else if (diff >= 45) pts = isFG ? 5 : 3.5;
  else if (diff >= 30) pts = isFG ? 4 : 3;
  else if (diff >= 18) pts = isFG ? 3 : 2;
  else if (diff >= 8 && tr <= 35) pts = isFG ? 2 : 1.5;

  // If both are elite, only give a tiny edge for the better rank.
  else if (tr <= 25 && or <= 25 && diff >= 5) pts = isFG ? 1.5 : 1;

  return pts;
}
function setupEdgePoints(v, scale=1){
  if (v == null || v === '' || !isFinite(Number(v))) return 0;
  const a = Math.abs(Number(v));
  if (a >= 20) return 8 * scale;
  if (a >= 12) return 6 * scale;
  if (a >= 7) return 4 * scale;
  if (a >= 3) return 2 * scale;
  return 0;
}
function setupAddDriver(arr, label, pts, text){
  if (!pts) return;
  arr.push({label, pts:Number(pts), text});
}
function setupContextNumber(obj, keys){
  obj = obj || {};
  for (const k of keys){
    if (obj[k] != null && obj[k] !== '' && isFinite(Number(obj[k]))) return Number(obj[k]);
  }
  const lower = {};
  Object.keys(obj).forEach(k => lower[k.toLowerCase()] = obj[k]);
  for (const k of keys){
    const v = lower[String(k).toLowerCase()];
    if (v != null && v !== '' && isFinite(Number(v))) return Number(v);
  }
  return null;
}
function spreadSetupScoreForTeam(g, team){
  const opp = team === g.home_team ? g.away_team : g.home_team;
  const drivers = [];
  const warnings = [];

  let coach = 0;
  [
    ['coach_betting', 'FG'],
    ['coach_1h_betting', '1H'],
    ['coach_2h_betting', '2H']
  ].forEach(([key, label]) => {
    let row = typeof betCoachRank === 'function' ? betCoachRank(team, key) : null;
    let oppRow = typeof betCoachRank === 'function' ? betCoachRank(opp, key) : null;

    // Fallback to the same helpers used by the visible Coach ATS rank strip.
    // Some rows exist but do not expose ats_rank through betCoachRank(), so also
    // fallback when the rank field itself is missing.
    if (!row || row.ats_rank == null) {
      if (key === 'coach_betting' && typeof coachForTeam === 'function') row = coachForTeam(team);
      if (key === 'coach_1h_betting' && typeof coachHalfByTeam === 'function') row = coachHalfByTeam(team, '1h');
      if (key === 'coach_2h_betting' && typeof coachHalfByTeam === 'function') row = coachHalfByTeam(team, '2h');
    }
    if (!oppRow || oppRow.ats_rank == null) {
      if (key === 'coach_betting' && typeof coachForTeam === 'function') oppRow = coachForTeam(opp);
      if (key === 'coach_1h_betting' && typeof coachHalfByTeam === 'function') oppRow = coachHalfByTeam(opp, '1h');
      if (key === 'coach_2h_betting' && typeof coachHalfByTeam === 'function') oppRow = coachHalfByTeam(opp, '2h');
    }

    const tr = row && (row.ats_rank ?? row.rank);
    const or = oppRow && (oppRow.ats_rank ?? oppRow.rank);

    const pts = setupCoachRankEdgePoints(tr, or, label);
    if (pts > 0) {
      coach += pts;
      setupAddDriver(drivers, 'Coach', pts, `${label} coach ATS rank edge (#${tr} vs #${or})`);
    }

    const oppPts = setupCoachRankEdgePoints(or, tr, label);
    if (oppPts >= 4) {
      warnings.push(`${label} coach ATS profile leans ${opp} (#${or} vs #${tr})`);
    }
  });

  // Graded matchup/system triggers if present.
  const triggerRows = Array.isArray(DB.matchup_system_triggers_2026) ? DB.matchup_system_triggers_2026 : [];
  const trig = triggerRows.filter(r => matchupNormName(r.team) === matchupNormName(team) && (!r.opponent || matchupNormName(r.opponent) === matchupNormName(opp)) && (!r.week || Number(r.week) === Number(g.week)));
  trig.slice(0,4).forEach(r => {
    const grade = String(r.grade || r.system_grade || '').toUpperCase();
    let pts = 0;
    if (grade.startsWith('A+')) pts = 11;
    else if (grade.startsWith('A')) pts = 9;
    else if (grade.startsWith('B+')) pts = 7;
    else if (grade.startsWith('B')) pts = 5;
    if (pts) {
      coach += pts;
      setupAddDriver(drivers, 'System', pts, `${grade} ${r.system_type || r.system_name || 'system trigger'}`);
    }
  });

  coach = setupClamp(coach, 0, 30);

  let schedule = 0;
  const flags = typeof betSituationalFlags === 'function' ? (betSituationalFlags(g, team) || []) : [];
  const oppFlags = typeof betSituationalFlags === 'function' ? (betSituationalFlags(g, opp) || []) : [];
  const flagText = JSON.stringify(flags).toLowerCase();
  const oppFlagText = JSON.stringify(oppFlags).toLowerCase();

  if (flagText.includes('bye')) {
    schedule += 6;
    setupAddDriver(drivers, 'Schedule', 6, `${team} off bye/rest advantage`);
  }
  if (oppFlagText.includes('short') || oppFlagText.includes('b2b') || oppFlagText.includes('road')) {
    schedule += 6;
    setupAddDriver(drivers, 'Schedule', 6, `${opp} adverse rest/travel spot`);
  }
  if (flagText.includes('short') || flagText.includes('b2b road')) {
    schedule -= 5;
    warnings.push(`${team} has adverse rest/travel spot`);
  }
  schedule = setupClamp(schedule, 0, 20);

  let style = 0;

  // Projection support acts as the current surrogate for market spread.
  // This does not mean "bet it" by itself; it tells us whether the model's spread
  // side lines up with the matchup setup.
  const projMargin = g.projected_margin_home != null && isFinite(Number(g.projected_margin_home)) ? Number(g.projected_margin_home) : null;
  if (projMargin != null) {
    const projectedSide = projMargin > 0 ? g.home_team : g.away_team;
    const absProj = Math.abs(projMargin);
    if (projectedSide === team) {
      let pts = 0;
      if (absProj >= 21) pts = 8;
      else if (absProj >= 14) pts = 7;
      else if (absProj >= 7) pts = 5;
      else if (absProj >= 3) pts = 3;
      if (pts) {
        style += pts;
        setupAddDriver(drivers, 'Projection', pts, `Projected spread supports ${team} by ${absProj.toFixed(1)}`);
      }
    }
  }

  const edge = matchupForGameTeam(g, team);
  const oppEdge = matchupForGameTeam(g, opp);

  if (edge) {
    [
      ['Passing matchup', edge.pass_off_edge],
      ['Rushing matchup', edge.rush_off_edge],
      ['Explosive matchup', edge.explosive_edge],
      ['Havoc/pressure matchup', edge.havoc_edge],
      ['Pass rush/protection', edge.pass_rush_edge],
    ].forEach(([label, val]) => {
      if (val == null || !isFinite(Number(val))) return;
      const n = Number(val);
      if (n > 0.5) {
        const pts = setupEdgePoints(n, 1);
        style += pts;
        setupAddDriver(drivers, 'Style', pts, `${label} favors ${team}`);
      } else if (n < -7) {
        warnings.push(`${label} favors ${opp}`);
      }
    });
  } else {
    warnings.push('Production matchup edge rows missing for this side');
  }

  // Team style profile proxies.
  const s = typeof styleForTeam === 'function' ? (styleForTeam(team) || {}) : {};
  const os = typeof styleForTeam === 'function' ? (styleForTeam(opp) || {}) : {};
  const offScore = setupContextNumber(s, ['offense_score','off_eff_score','explosive_score']);
  const oppDef = setupContextNumber(os, ['defense_score','def_eff_score','ppa_prevent_score','expl_prevent_score']);
  if (offScore != null && oppDef != null) {
    const diff = offScore - oppDef;
    if (diff >= 12) {
      const pts = diff >= 25 ? 6 : 4;
      style += pts;
      setupAddDriver(drivers, 'Style', pts, 'Offensive style profile has matchup room');
    } else if (diff <= -18) {
      warnings.push('Opponent defensive style profile creates resistance');
    }
  }
  style = setupClamp(style, 0, 25);

  let sos = 0;
  const ctx = typeof sosContextForTeam === 'function' ? (sosContextForTeam(team, g) || {}) : {};
  const oppCtx = typeof sosContextForTeam === 'function' ? (sosContextForTeam(opp, g) || {}) : {};
  const step = setupContextNumber(ctx, ['step_up_down','step_delta','rating_step','current_opponent_rating_delta']);
  const oppStep = setupContextNumber(oppCtx, ['step_up_down','step_delta','rating_step','current_opponent_rating_delta']);
  if (step != null && step < -3) {
    sos += 4;
    setupAddDriver(drivers, 'SOS', 4, `${team} steps down in opponent class`);
  }
  if (oppStep != null && oppStep > 3) {
    sos += 4;
    setupAddDriver(drivers, 'SOS', 4, `${opp} steps up in opponent class`);
  }
  const tRank = betTeamObj(team);
  const oRank = betTeamObj(opp);
  if (tRank && oRank && isFinite(Number(tRank.rank)) && isFinite(Number(oRank.rank))) {
    const rankDiff = Number(oRank.rank) - Number(tRank.rank);
    if (rankDiff >= 35) {
      sos += 3;
      setupAddDriver(drivers, 'SOS', 3, 'Power-rating class edge');
    }
  }
  sos = setupClamp(sos, 0, 10);

  let luck = 0;
  const tc = typeof teamContextFor === 'function' ? (teamContextFor(team) || {}) : {};
  const oc = typeof teamContextFor === 'function' ? (teamContextFor(opp) || {}) : {};
  const consistency = setupContextNumber(tc, ['consistency','consistency_rating','consistency_score']);
  const oppConsistency = setupContextNumber(oc, ['consistency','consistency_rating','consistency_score']);
  const luckVal = setupContextNumber(tc, ['luck','luck_rating','luck_score']);
  const oppLuck = setupContextNumber(oc, ['luck','luck_rating','luck_score']);
  if (consistency != null && oppConsistency != null) {
    const diff = consistency - oppConsistency;
    if (diff >= 10) {
      luck += 4;
      setupAddDriver(drivers, 'Luck/Consistency', 4, 'Consistency edge');
    } else if (diff <= -15) {
      luck -= 4;
      warnings.push('Consistency profile favors opponent');
    }
  }
  if (luckVal != null && oppLuck != null) {
    if (luckVal < oppLuck - 12) {
      luck += 3;
      setupAddDriver(drivers, 'Luck/Consistency', 3, 'Potential luck-regression support');
    } else if (luckVal > oppLuck + 18) {
      luck -= 3;
      warnings.push('Luck profile may be inflated');
    }
  }
  luck = setupClamp(luck, -10, 10);

  let penalties = 0;
  if (!edge) penalties -= 4;
  if (g.away_conference === 'FCS' || g.home_conference === 'FCS' || g.away_conference === 'Non-FBS' || g.home_conference === 'Non-FBS') {
    penalties -= 5;
    warnings.push('FCS/Non-FBS opponent creates data uncertainty');
  }

  const projectedSide = Number(g.projected_margin_home || 0) > 0 ? g.home_team : g.away_team;
  if (g.projected_margin_home != null && isFinite(Number(g.projected_margin_home)) && Math.abs(Number(g.projected_margin_home)) >= 3 && projectedSide !== team) {
    penalties -= 3;
    warnings.push('Setup side differs from projected favorite');
  }

  penalties = setupClamp(penalties, -20, 0);

  const raw = coach + schedule + style + sos + luck + penalties;
  const score = setupClamp(raw, 0, 100);

  return {
    team,
    opponent: opp,
    score,
    coach,
    schedule,
    style,
    sos,
    luck,
    penalties,
    drivers,
    warnings
  };
}
function computeSpreadBetSetup(g){
  const away = spreadSetupScoreForTeam(g, g.away_team);
  const home = spreadSetupScoreForTeam(g, g.home_team);

  const diff = away.score - home.score;
  let winner = null;
  let loser = null;
  if (Math.abs(diff) >= 6) {
    winner = diff > 0 ? away : home;
    loser = diff > 0 ? home : away;
  }

  if (!winner) {
    const evenScore = Math.max(away.score, home.score);
    const grade = setupGrade(evenScore);
    return {side:'Even', winner:null, loser:null, away, home, score:evenScore, grade};
  }

  // Do not attach a team name to weak setup scores.
  if (winner.score < 35) {
    const evenScore = Math.max(away.score, home.score);
    const grade = setupGrade(evenScore);
    return {side:'Even', winner:null, loser:null, away, home, score:evenScore, grade};
  }

  const grade = setupGrade(winner.score);
  return {side:winner.team, winner, loser, away, home, score:winner.score, grade};
}
function spreadSetupCompactLabel(g){
  const s = computeSpreadBetSetup(g);
  if (!s.winner || s.score < 35) {
    return `<span class="spread-setup-compact muted">No edge</span>`;
  }
  return `<span class="spread-setup-compact">
    <span class="setup-team">${teamLabel(s.winner.team)}</span>
    <span style="font-weight:1000;white-space:nowrap">${s.grade.checks} ${Math.round(s.score)}</span>
  </span>`;
}
function spreadSetupDetailCard(g){
  const s = computeSpreadBetSetup(g);
  const grade = s.grade;
  const winner = s.winner;
  const away = s.away;
  const home = s.home;

  const bucketHtml = (label, value, maxLabel='') => `<div class="spread-setup-bucket"><div class="label">${label}</div><div class="value">${Number(value).toFixed(1)}${maxLabel}</div></div>`;

  const active = winner || (away.score >= home.score ? away : home);
  const drivers = [...(active.drivers || [])].sort((a,b)=>Math.abs(b.pts)-Math.abs(a.pts)).slice(0,8);
  const warnings = [...(active.warnings || [])].slice(0,8);

  const projected = g.projected_margin_home == null || !isFinite(Number(g.projected_margin_home))
    ? 'Projected spread not loaded'
    : `Projection: ${(Number(g.projected_margin_home) > 0 ? g.home_team : g.away_team)} -${Math.abs(Number(g.projected_margin_home)).toFixed(1)}`;

  return `<div class="spread-setup-card">
    <div class="spread-setup-head">
      <div>
        <div class="spread-setup-title">Spread Bet Setup Score</div>
        <div class="spread-setup-sub">${escapeHtml(projected)} · setup score is matchup/context only, not a final bet signal.</div>
      </div>
      <div class="spread-setup-grade ${grade.cls}">
        ${winner ? `${teamLabel(winner.team)} ${grade.checks} ${grade.grade}` : `No edge`}
        <span>${Math.round(s.score)}/100</span>
      </div>
    </div>
    <div class="spread-setup-grid">
      ${bucketHtml('Coach/System', active.coach, '/30')}
      ${bucketHtml('Schedule', active.schedule, '/20')}
      ${bucketHtml('Style/Matchup', active.style, '/25')}
      ${bucketHtml('SOS/Step', active.sos, '/10')}
      ${bucketHtml('Luck/Cons', active.luck, '')}
      ${bucketHtml('Warnings', active.penalties, '')}
    </div>
    <div class="spread-setup-lists">
      <div>
        <div class="spread-setup-list-title">Main drivers</div>
        <div class="spread-setup-list">
          ${drivers.length ? drivers.map(d=>`<div class="spread-setup-item"><b>${escapeHtml(d.label)} +${Number(d.pts).toFixed(1)}</b> · ${escapeHtml(d.text)}</div>`).join('') : '<div class="spread-setup-item muted">No major setup drivers found.</div>'}
        </div>
      </div>
      <div>
        <div class="spread-setup-list-title">Warnings / checks</div>
        <div class="spread-setup-list">
          ${warnings.length ? warnings.map(w=>`<div class="spread-setup-item spread-setup-warning">– ${escapeHtml(w)}</div>`).join('') : '<div class="spread-setup-item muted">No major warnings found.</div>'}
        </div>
      </div>
    </div>
  </div>`;
}
function matchupCompactLabel(g){
  return spreadSetupCompactLabel(g);
}
function matchupEdgeWinner(team, opponent, value){
  if (value == null || value === '' || !isFinite(Number(value))) return 'No data';
  const n = Number(value);
  if (Math.abs(n) < 0.5) return 'Even';
  return n > 0 ? `${escapeHtml(team)} ${matchupSigned(n)}` : `${escapeHtml(opponent)} ${matchupSigned(Math.abs(n))}`;
}
function talentRows(){ return Array.isArray(DB.team_position_talent_ratings) ? DB.team_position_talent_ratings : []; }
function talentFor(team, group){
  const tn = matchupNormName(team);
  const matches = talentRows().filter(r => matchupNormName(r.team) === tn && String(r.position_group) === group);
  if (!matches.length) return null;

  // Prefer real populated talent rows over scaffold/placeholder rows.
  const populated = matches.find(r => r.final_talent_score != null && r.final_talent_score !== '' && isFinite(Number(r.final_talent_score)));
  return populated || matches[0] || null;
}
function talentScore(team, group){
  const r = talentFor(team, group);
  if (!r || r.final_talent_score == null || !isFinite(Number(r.final_talent_score))) return null;
  return Number(r.final_talent_score);
}

function talentRatingDetailLine(team, opp, offenseGroup, defenseGroup){
  const off = talentScore(team, offenseGroup);
  const def = talentScore(opp, defenseGroup);

  const offTxt = off == null ? 'No rating' : Number(off).toFixed(1);
  const defTxt = def == null ? 'No rating' : Number(def).toFixed(1);

  const labels = {
    'QB_WR_TE_vs_Coverage': 'QB/WR/TE',
    'OL_Run_Game_vs_Front_Seven': 'RB/OL',
    'OL_Pass_Pro_vs_Pass_Rush': 'OL/Pass Pro',
    'Explosive_Skill_vs_Explosive_Defense': 'Skill/Explosive',
    'DB_LB_Coverage': 'DB/LB Coverage',
    'DL_LB_Front_Seven': 'DL/LB Front',
    'DL_LB_Pass_Rush': 'DL/LB Rush'
  };

  const offLabel = labels[offenseGroup] || offenseGroup;
  const defLabel = labels[defenseGroup] || defenseGroup;

  return `<div class="talent-detail-line">${escapeHtml(team)} ${escapeHtml(offLabel)} <b>${offTxt}</b> <span>vs</span> ${escapeHtml(opp)} ${escapeHtml(defLabel)} <b>${defTxt}</b></div>`;
}

function talentEdgeRow(team, opp, offenseGroup, defenseGroup){
  const offScore = talentScore(team, offenseGroup);
  const defScore = talentScore(opp, defenseGroup);
  const detail = talentRatingDetailLine(team, opp, offenseGroup, defenseGroup);

  if (offScore == null || defScore == null) {
    return `<div class="matchup-grade-row muted-grade"><span>Talent Edge</span><strong title="Missing position-group talent data for one or both sides.">No data</strong></div>${detail}`;
  }

  const edge = offScore - defScore;
  const cls = matchupClass(edge);
  const label = Math.abs(edge) < 0.5 ? 'Even' : edge > 0 ? `${escapeHtml(team)} ${matchupSigned(edge)}` : `${escapeHtml(opp)} ${matchupSigned(Math.abs(edge))}`;
  const title = `${team} ${offenseGroup}: ${offScore.toFixed(1)} vs ${opp} ${defenseGroup}: ${defScore.toFixed(1)}`;
  return `<div class="matchup-grade-row"><span>Talent Edge</span><strong class="${cls}" title="${escapeHtml(title)}">${label}</strong></div>${detail}`;
}

function advTeamInitials(team){
  const parts = String(team || '?').replace(/[^A-Za-z0-9 ]+/g, ' ').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
function advTeamLogo(team){
  try {
    const img = teamImageImg(team);
    if (img && String(img).trim()) return img;
  } catch(e) {}
  return `<span class="adv-initials">${escapeHtml(advTeamInitials(team))}</span>`;
}
function edgeBlocks(value){
  if (value == null || value === '' || !isFinite(Number(value))) return 0;
  const n = Math.abs(Number(value));
  if (n < 0.5) return 0;
  if (n < 2.5) return 1;
  if (n < 5.0) return 2;
  if (n < 8.0) return 3;
  if (n < 12.0) return 4;
  return 5;
}
function matchupAdvantageBar(leftTeam, rightTeam, value, label='Edge'){
  const emptyBlocks = [1,2,3,4,5].map(() => `<span class="adv-block"></span>`).join('');

  if (value == null || value === '' || !isFinite(Number(value))) {
    return `<div class="advantage-wrap">
      <div class="advantage-label-row"><span>${escapeHtml(label)}</span><strong class="adv-even">No data</strong></div>
      <div class="advantage-bar-row">
        <span class="adv-logo">${advTeamLogo(leftTeam)}</span>
        <div class="adv-half adv-left">${emptyBlocks}</div>
        <span class="adv-mid"></span>
        <div class="adv-half adv-right">${emptyBlocks}</div>
        <span class="adv-logo">${advTeamLogo(rightTeam)}</span>
      </div>
    </div>`;
  }

  const n = Number(value);
  const blocks = edgeBlocks(n);
  const leftOwns = n > 0;
  const rightOwns = n < 0;

  const displayTeam = Math.abs(n) < 0.5 ? 'Even' : (leftOwns ? leftTeam : rightTeam);
  const displayVal = Math.abs(n) < 0.5 ? '' : ` ${matchupSigned(Math.abs(n))}`;

  const leftBlocks = [5,4,3,2,1].map(i => {
    const filled = leftOwns && i <= blocks;
    return `<span class="adv-block ${filled ? 'adv-fill adv-fill-left' : ''}"></span>`;
  }).join('');

  const rightBlocks = [1,2,3,4,5].map(i => {
    const filled = rightOwns && i <= blocks;
    return `<span class="adv-block ${filled ? 'adv-fill adv-fill-right' : ''}"></span>`;
  }).join('');

  const cls = Math.abs(n) < 0.5 ? 'adv-even' : leftOwns ? 'adv-left-text' : 'adv-right-text';

  return `<div class="advantage-wrap">
    <div class="advantage-label-row">
      <span>${escapeHtml(label)}</span>
      <strong class="${cls}">${escapeHtml(displayTeam)}${escapeHtml(displayVal)}</strong>
    </div>
    <div class="advantage-bar-row" title="${escapeHtml(label)}: ${escapeHtml(displayTeam)}${escapeHtml(displayVal)}">
      <span class="adv-logo">${advTeamLogo(leftTeam)}</span>
      <div class="adv-half adv-left">${leftBlocks}</div>
      <span class="adv-mid"></span>
      <div class="adv-half adv-right">${rightBlocks}</div>
      <span class="adv-logo">${advTeamLogo(rightTeam)}</span>
    </div>
  </div>`;
}
function talentEdgeValue(team, opp, offenseGroup, defenseGroup){
  const offScore = talentScore(team, offenseGroup);
  const defScore = talentScore(opp, defenseGroup);
  if (offScore == null || defScore == null) return null;
  return offScore - defScore;
}
function matchupTalentAdvantageBar(team, opp, offenseGroup, defenseGroup){
  return matchupAdvantageBar(team, opp, talentEdgeValue(team, opp, offenseGroup, defenseGroup), 'Talent Edge');
}


function matchupGroupLabel(group){
  const labels = {
    'QB_WR_TE_vs_Coverage': 'QB/WR/TE',
    'OL_Run_Game_vs_Front_Seven': 'RB/OL',
    'OL_Pass_Pro_vs_Pass_Rush': 'OL Pass Pro',
    'Explosive_Skill_vs_Explosive_Defense': 'Skill',
    'DB_LB_Coverage': 'DB/LB',
    'DL_LB_Front_Seven': 'DL/LB Front',
    'DL_LB_Pass_Rush': 'DL/LB Rush'
  };
  return labels[group] || group;
}
function ratingColorClass(score){
  if (score == null || score === '' || !isFinite(Number(score))) return 'rating-na';
  const n = Number(score);
  if (n >= 85) return 'rating-elite';
  if (n >= 75) return 'rating-good';
  if (n >= 65) return 'rating-mid';
  return 'rating-bad';
}
function matchupRatingChip(team, group){
  const score = talentScore(team, group);
  const txt = score == null ? '—' : Number(score).toFixed(1);
  return `<span class="vg-rating-chip ${ratingColorClass(score)}">${escapeHtml(matchupGroupLabel(group))} <b>${txt}</b></span>`;
}
function matchupEdgePill(label, team, opponent, value){
  if (value == null || value === '' || !isFinite(Number(value))) {
    return `<span class="vg-edge-pill neutral"><b>${escapeHtml(label)}</b> No data</span>`;
  }
  const n = Number(value);
  if (Math.abs(n) < 0.5) {
    return `<span class="vg-edge-pill neutral"><b>${escapeHtml(label)}</b> Even</span>`;
  }
  const owner = n > 0 ? team : opponent;
  const cls = n > 0 ? 'left' : 'right';
  return `<span class="vg-edge-pill ${cls}"><b>${escapeHtml(label)}</b> ${escapeHtml(owner)} ${matchupSigned(Math.abs(n))}</span>`;
}
function matchupTalentEdgeValue(team, opponent, offenseGroup, defenseGroup){
  const off = talentScore(team, offenseGroup);
  const def = talentScore(opponent, defenseGroup);
  if (off == null || def == null) return null;
  return off - def;
}
function matchupTalentVsLine(team, opponent, offenseGroup, defenseGroup){
  return `<div class="vg-vs-line">
    <span class="vg-team-mini">${teamLabel(team)}</span>
    ${matchupRatingChip(team, offenseGroup)}
    <span class="vg-vs">vs</span>
    ${matchupRatingChip(opponent, defenseGroup)}
    <span class="vg-team-mini">${teamLabel(opponent)}</span>
  </div>`;
}

function matchupPositionCard(title, subtitle, team, opponent, value, read, offenseTalentGroup=null, defenseTalentGroup=null){
  const talentValue = offenseTalentGroup && defenseTalentGroup
    ? matchupTalentEdgeValue(team, opponent, offenseTalentGroup, defenseTalentGroup)
    : null;

  return `<div class="matchup-card matchup-position-card vg-matchup-card">
    <div class="vg-card-head">
      <div>
        <div class="matchup-label">${escapeHtml(title)}</div>
        <div class="matchup-position-sub">${escapeHtml(subtitle)}</div>
      </div>
    </div>

    ${offenseTalentGroup && defenseTalentGroup ? matchupTalentVsLine(team, opponent, offenseTalentGroup, defenseTalentGroup) : ''}

    <div class="vg-edge-row">
      ${matchupEdgePill('Prod', team, opponent, value)}
      ${matchupEdgePill('Talent', team, opponent, talentValue)}
    </div>
  </div>`;
}
function styleRows(){ return Array.isArray(DB.team_style_profiles) ? DB.team_style_profiles : []; }
function styleForTeam(team){
  const tn = matchupNormName(team);
  return styleRows().find(s => matchupNormName(s.team) === tn) || null;
}
function styleScoreClass(score){
  if (score == null || score === '' || !isFinite(Number(score))) return 'style-neutral';
  const n = Number(score);
  if (n >= 67) return 'style-good';
  if (n <= 33) return 'style-bad';
  return 'style-neutral';
}
function styleScoreText(score){
  if (score == null || score === '' || !isFinite(Number(score))) return '';
  return ` <em>${Math.round(Number(score))}</em>`;
}
function firstStyleValue(s, names){
  for (const name of names) {
    if (s && s[name] != null && s[name] !== '' && isFinite(Number(s[name]))) {
      return Number(s[name]);
    }
  }
  return null;
}

function stylePill(label, score){
  if (score == null || score === '' || !isFinite(Number(score))) return '';
  return `<span class="style-pill ${styleScoreClass(score)}"><b>${escapeHtml(label)}</b><em>${Math.round(Number(score))}</em></span>`;
}
function styleRatePill(label, rate){
  if (rate == null || rate === '' || !isFinite(Number(rate))) return '';
  const pct = Math.round(Number(rate) * 100);
  const cls = pct >= 58 ? 'style-good' : pct <= 42 ? 'style-bad' : 'style-neutral';
  return `<span class="style-pill ${cls}"><b>${escapeHtml(label)}</b><em>${pct}%</em></span>`;
}
function styleTextPill(label, value, cls='style-neutral'){
  if (!value || value === '—') return '';
  return `<span class="style-pill ${cls}"><b>${escapeHtml(label)}</b><em>${escapeHtml(value)}</em></span>`;
}
function downSplitRows(){ return Array.isArray(DB.team_down_split_tendencies) ? DB.team_down_split_tendencies : []; }
function downSplitForTeam(team){
  const tn = matchupNormName(team);
  return downSplitRows().find(r => matchupNormName(r.team) === tn) || null;
}
function ratePct(rate){
  if (rate == null || rate === '' || !isFinite(Number(rate))) return '—';
  return `${Math.round(Number(rate) * 100)}%`;
}
function tendencyForTeam(team){
  const s = styleForTeam(team);
  const d = downSplitForTeam(team);
  return {
    passRate: s && s.pass_rate != null ? Number(s.pass_rate) : (d && d.overall_pass_rate != null ? Number(d.overall_pass_rate) : null),
    rushRate: s && s.rush_rate != null ? Number(s.rush_rate) : (d && d.overall_rush_rate != null ? Number(d.overall_rush_rate) : null),
    standardPassRate: d && d.standard_down_pass_rate != null ? Number(d.standard_down_pass_rate) : null,
    standardRushRate: d && d.standard_down_rush_rate != null ? Number(d.standard_down_rush_rate) : null,
    passingDownPassRate: d && d.passing_down_pass_rate != null ? Number(d.passing_down_pass_rate) : null,
    passingDownRushRate: d && d.passing_down_rush_rate != null ? Number(d.passing_down_rush_rate) : null,
    playCallStyle: s && s.play_call_style ? String(s.play_call_style) : 'unknown',
    explosiveScore: s && s.explosive_score != null ? Number(s.explosive_score) : null,
    havocAvoidScore: s && s.havoc_risk_score != null ? Number(s.havoc_risk_score) : null
  };
}
function priorityLabel(score){
  if (score >= 65) return 'High';
  if (score >= 45) return 'Med';
  return 'Low';
}
function priorityClass(score){
  if (score >= 65) return 'style-good';
  if (score >= 45) return 'style-neutral';
  return 'style-bad';
}
function miniMatchupAdvantageBar(leftTeam, rightTeam, value){
  if (value == null || value === '' || !isFinite(Number(value))) {
    return `<div class="priority-mini-bar">
      <span class="priority-mini-team priority-mini-logo">${advTeamLogo(leftTeam)}</span>
      <div class="priority-mini-half">${[1,2,3,4,5].map(()=>`<span></span>`).join('')}</div>
      <i></i>
      <div class="priority-mini-half">${[1,2,3,4,5].map(()=>`<span></span>`).join('')}</div>
      <span class="priority-mini-team priority-mini-logo">${advTeamLogo(rightTeam)}</span>
    </div>`;
  }

  const n = Number(value);
  const blocks = edgeBlocks(n);
  const leftOwns = n > 0;
  const rightOwns = n < 0;

  const leftBlocks = [5,4,3,2,1].map(i => {
    const filled = leftOwns && i <= blocks;
    return `<span class="${filled ? 'mini-fill-left' : ''}"></span>`;
  }).join('');

  const rightBlocks = [1,2,3,4,5].map(i => {
    const filled = rightOwns && i <= blocks;
    return `<span class="${filled ? 'mini-fill-right' : ''}"></span>`;
  }).join('');

  return `<div class="priority-mini-bar">
    <span class="priority-mini-team priority-mini-logo">${advTeamLogo(leftTeam)}</span>
    <div class="priority-mini-half">${leftBlocks}</div>
    <i></i>
    <div class="priority-mini-half">${rightBlocks}</div>
    <span class="priority-mini-team priority-mini-logo">${advTeamLogo(rightTeam)}</span>
  </div>`;
}
function matchupPriorityItems(r){
  if (!r) return [];
  const t = tendencyForTeam(r.team);
  const passRate = t.passRate == null ? 0.50 : t.passRate;
  const rushRate = t.rushRate == null ? 0.50 : t.rushRate;
  const stdRushRate = t.standardRushRate == null ? rushRate : t.standardRushRate;
  const passDownPassRate = t.passingDownPassRate == null ? passRate : t.passingDownPassRate;
  const explosive = t.explosiveScore == null ? 50 : t.explosiveScore;
  const havocAvoid = t.havocAvoidScore == null ? 50 : t.havocAvoidScore;

  const pressureEdge = r.pass_protection_edge == null ? 0 : Math.abs(Number(r.pass_protection_edge));
  const passEdge = r.pass_off_edge == null ? 0 : Math.abs(Number(r.pass_off_edge));
  const rushEdge = r.rush_off_edge == null ? 0 : Math.abs(Number(r.rush_off_edge));
  const explosiveEdge = r.explosive_edge == null ? 0 : Math.abs(Number(r.explosive_edge));

  const passPriority = ((passRate * 35) + (passDownPassRate * 35)) + Math.min(passEdge * 2, 20);
  const rushPriority = ((rushRate * 30) + (stdRushRate * 40)) + Math.min(rushEdge * 2, 20);
  const pressurePriority = (passDownPassRate * 60) + Math.min(pressureEdge * 2.2, 35) + (havocAvoid < 35 ? 10 : 0);
  const explosivePriority = (explosive * 0.55) + Math.min(explosiveEdge * 2.0, 30);

  const items = [
    {
      key: 'pass',
      title: 'Passing Game / Skill vs Coverage',
      score: passPriority,
      edge: r.pass_off_edge,
      note: `${Math.round(passRate*100)}% overall pass; ${Math.round(passDownPassRate*100)}% pass on passing downs; performance edge ${matchupSigned(r.pass_off_edge)}.`
    },
    {
      key: 'rush',
      title: 'Run Game / OL vs Front Seven',
      score: rushPriority,
      edge: r.rush_off_edge,
      note: `${Math.round(rushRate*100)}% overall rush; ${Math.round(stdRushRate*100)}% rush on standard downs; performance edge ${matchupSigned(r.rush_off_edge)}.`
    },
    {
      key: 'pressure',
      title: 'Protection vs Pressure',
      score: pressurePriority,
      edge: r.pass_protection_edge,
      note: `Weighted by passing-down pass rate, protection risk, and opponent havoc profile.`
    },
    {
      key: 'explosive',
      title: 'Explosive Plays',
      score: explosivePriority,
      edge: r.explosive_edge,
      note: `Explosive profile ${Math.round(explosive)}/100; performance edge ${matchupSigned(r.explosive_edge)}.`
    }
  ];

  return items.sort((a,b) => b.score - a.score);
}
function matchupPriorityHtml(r){
  const items = matchupPriorityItems(r).slice(0, 3);
  if (!items.length) return '';
  return `<div class="matchup-priority-box">
    <div class="matchup-priority-title">Top matchups that matter for ${teamLabel(r.team)} offense</div>
    <div class="matchup-priority-list">
      ${items.map((it, idx) => `<div class="matchup-priority-item">
        <span class="matchup-priority-rank">${idx+1}</span>
        <div class="matchup-priority-main">
          <div class="priority-title-row"><b>${escapeHtml(it.title)}</b> <span class="style-pill ${priorityClass(it.score)}"><b>${priorityLabel(it.score)}</b><em>${Math.round(it.score)}</em></span></div>
          ${miniMatchupAdvantageBar(r.team, r.opponent, it.edge)}
          <small>${escapeHtml(it.note)}</small>
        </div>
      </div>`).join('')}
    </div>
  </div>`;
}
function styleProfileHtml(team){
  const s = styleForTeam(team);
  if (!s) return '';
  const d = downSplitForTeam(team);

  return `<div class="team-style-box vg-style-box">
    <div class="team-style-title">${teamLabel(team)} profile <span class="team-style-scale">(0–100 percentile grades)</span></div>

    <div class="vg-style-section">
      <div class="vg-style-section-title">Offense</div>
      <div class="style-pill-row">
        ${stylePill('Off Success', s.offense_score)}
        ${stylePill('Expl', s.explosive_score)}
        ${styleRatePill('Pass', s.pass_rate)}
        ${styleRatePill('Rush', s.rush_rate)}
        ${d ? styleTextPill('Std Rush', ratePct(d.standard_down_rush_rate), d.standard_down_rush_rate >= .58 ? 'style-good' : d.standard_down_rush_rate <= .42 ? 'style-bad' : 'style-neutral') : ''}
        ${d ? styleTextPill('Pass Down', ratePct(d.passing_down_pass_rate), d.passing_down_pass_rate >= .65 ? 'style-good' : d.passing_down_pass_rate <= .50 ? 'style-bad' : 'style-neutral') : ''}
        ${stylePill('Havoc Avd', s.havoc_risk_score)}
      </div>
    </div>

    <div class="vg-style-section">
      <div class="vg-style-section-title">Defense</div>
      <div class="style-pill-row">
        ${stylePill('Success Prevent', firstStyleValue(s, ['defense_score']))}
        ${stylePill('PPA Prevent', firstStyleValue(s, ['ppa_prevent_score']))}
        ${stylePill('Finish Prevent', firstStyleValue(s, ['finishing_prevent_score']))}
        ${stylePill('Field Pos Def', firstStyleValue(s, ['field_position_prevent_score']))}
        ${stylePill('Expl Prevent', firstStyleValue(s, ['expl_prevent_score']))}
        ${stylePill('Havoc Cr', firstStyleValue(s, ['havoc_creation_score','pressure_score']))}
        ${stylePill('Run Defense', firstStyleValue(s, ['run_front_score','front_score']))}
      </div>
    </div>

    <div class="team-style-summary compact-summary">${escapeHtml(s.style_summary || '')}</div>
  </div>`;
}
function pressureConcernText(r){
  if (!r) return '';
  const team = r.team;
  const opp = r.opponent;
  const protection = r.pass_protection_edge == null ? null : Number(r.pass_protection_edge);
  if (protection != null && isFinite(protection) && protection < -5) {
    return `The protection/pressure matchup is the main disruption risk for ${team}'s offense, with ${opp} holding the production edge there.`;
  }
  if (protection != null && isFinite(protection) && protection > 5) {
    return `${team}'s protection/havoc-avoidance profile is a meaningful production advantage against ${opp}'s pressure profile.`;
  }
  return '';
}
function talentEdgeForPriority(r, key){
  if (!r) return null;
  const team = r.team, opp = r.opponent;

  if (key === 'pass') return talentEdgeValue(team, opp, 'QB_WR_TE_vs_Coverage', 'DB_LB_Coverage');
  if (key === 'rush') return talentEdgeValue(team, opp, 'OL_Run_Game_vs_Front_Seven', 'DL_LB_Front_Seven');
  if (key === 'pressure') return talentEdgeValue(team, opp, 'OL_Pass_Pro_vs_Pass_Rush', 'DL_LB_Pass_Rush');
  if (key === 'explosive') return talentEdgeValue(team, opp, 'Explosive_Skill_vs_Explosive_Defense', 'DB_LB_Coverage');

  // Fallback based on title, in case priority objects do not carry key.
  const title = String(r.title || '').toLowerCase();
  if (title.includes('pass')) return talentEdgeValue(team, opp, 'QB_WR_TE_vs_Coverage', 'DB_LB_Coverage');
  if (title.includes('run')) return talentEdgeValue(team, opp, 'OL_Run_Game_vs_Front_Seven', 'DL_LB_Front_Seven');
  if (title.includes('protection') || title.includes('pressure')) return talentEdgeValue(team, opp, 'OL_Pass_Pro_vs_Pass_Rush', 'DL_LB_Pass_Rush');
  if (title.includes('explosive')) return talentEdgeValue(team, opp, 'Explosive_Skill_vs_Explosive_Defense', 'DB_LB_Coverage');

  return null;
}

function matchupEdgeOwnerText(team, opp, value, label){
  if (value == null || value === '' || !isFinite(Number(value))) return `${label} is missing production data.`;
  const n = Number(value);
  if (Math.abs(n) < 0.5) return `${label} is close to even on production.`;
  return n > 0
    ? `${team} owns the production edge in ${label.toLowerCase()} (${matchupSigned(n)}).`
    : `${opp} owns the production counter in ${label.toLowerCase()} (${matchupSigned(Math.abs(n))}).`;
}

function talentAgreementText(team, opp, perfValue, talentValue){
  if (talentValue == null || talentValue === '' || !isFinite(Number(talentValue))) {
    return 'Talent data is not available for this matchup yet.';
  }

  const p = Number(perfValue || 0);
  const t = Number(talentValue || 0);

  if (Math.abs(t) < 0.5) return 'Talent is close to even.';

  const talentOwner = t > 0 ? team : opp;

  if (Math.abs(p) < 0.5) {
    return `Talent leans ${talentOwner}, but production is closer to even.`;
  }

  const perfOwner = p > 0 ? team : opp;

  if (perfOwner === talentOwner) {
    return `Performance and talent both lean ${perfOwner}, making this a higher-confidence edge.`;
  }

  return `Performance leans ${perfOwner}, but talent leans ${talentOwner}; treat this as a more volatile edge.`;
}

function matchupSideRead(r){
  if (!r) return '';
  const team = r.team, opp = r.opponent;
  const priorities = matchupPriorityItems(r).slice(0, 3);

  if (!priorities.length) {
    return `Production profile is incomplete for ${team}'s offense.`;
  }

  const top = priorities[0];
  const second = priorities[1];

  const topTalent = talentEdgeForPriority(r, top.key);
  const secondTalent = second ? talentEdgeForPriority(r, second.key) : null;

  let txt = `${team}'s most important matchup is ${top.title.toLowerCase()}. `;
  txt += matchupEdgeOwnerText(team, opp, top.edge, top.title) + ' ';
  txt += talentAgreementText(team, opp, top.edge, topTalent);

  if (second) {
    txt += ` The secondary swing point is ${second.title.toLowerCase()}. `;
    txt += matchupEdgeOwnerText(team, opp, second.edge, second.title) + ' ';
    txt += talentAgreementText(team, opp, second.edge, secondTalent);
  }

  const pressure = pressureConcernText(r);
  if (pressure) txt += ` ${pressure}`;

  txt += ' This read is still preseason/projection-based and does not yet include injuries or 2026 in-season form.';

  return txt;
}
function matchupPressureCard(team, opponent, protectionValue){
  const n = protectionValue == null || protectionValue === '' || !isFinite(Number(protectionValue)) ? null : Number(protectionValue);
  const label = n != null && n < -0.5 ? 'Pressure' : 'Protection';
  const talentValue = matchupTalentEdgeValue(team, opponent, 'OL_Pass_Pro_vs_Pass_Rush', 'DL_LB_Pass_Rush');

  return `<div class="matchup-card matchup-position-card vg-matchup-card">
    <div class="vg-card-head">
      <div>
        <div class="matchup-label">Protection vs Pressure</div>
        <div class="matchup-position-sub">OL pass pro vs opponent DL/LB rush</div>
      </div>
    </div>

    ${matchupTalentVsLine(team, opponent, 'OL_Pass_Pro_vs_Pass_Rush', 'DL_LB_Pass_Rush')}

    <div class="vg-edge-row">
      ${matchupEdgePill(label, team, opponent, n)}
      ${matchupEdgePill('Talent', team, opponent, talentValue)}
    </div>
  </div>`;
}

function matchupGradeClass(v){
  if (v == null || v === '' || !isFinite(Number(v))) return 'grade-na';
  const n = Number(v);
  if (n >= 67) return 'grade-good';
  if (n >= 34) return 'grade-mid';
  return 'grade-bad';
}
function matchupGradeValue(v){
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  return `${Math.round(Number(v))}`;
}
function matchupCompareChip(leftLabel, leftValue, rightLabel, rightValue, note='', leftTeam='', rightTeam=''){
  const lv = leftValue == null || leftValue === '' || !isFinite(Number(leftValue)) ? null : Number(leftValue);
  const rv = rightValue == null || rightValue === '' || !isFinite(Number(rightValue)) ? null : Number(rightValue);
  let edgeHtml = '';
  if (lv != null && rv != null) {
    const diff = lv - rv;
    const owner = Math.abs(diff) < 0.5 ? 'Even' : diff > 0 ? leftTeam : rightTeam;
    const edgeClass = Math.abs(diff) < 0.5 ? 'edge-even' : diff > 0 ? 'edge-left' : 'edge-right';
    const edgeText = Math.abs(diff) < 0.5 ? 'Even' : `${owner} +${Math.abs(diff).toFixed(0)}`;
    edgeHtml = `<div class="matchup-compare-edge ${edgeClass}">${escapeHtml(edgeText)}</div>`;
  }

  return `<div class="matchup-compare-chip">
    <div class="matchup-compare-row">
      <div class="matchup-compare-side ${matchupGradeClass(leftValue)}">
        <span>${escapeHtml(leftLabel)}</span>
        <b>${matchupGradeValue(leftValue)}</b>
      </div>
      <div class="matchup-compare-vs">vs</div>
      <div class="matchup-compare-side ${matchupGradeClass(rightValue)}">
        <span>${escapeHtml(rightLabel)}</span>
        <b>${matchupGradeValue(rightValue)}</b>
      </div>
    </div>
    ${edgeHtml}
    ${note ? `<small>${escapeHtml(note)}</small>` : ''}
  </div>`;
}
function matchupPctValue(v){
  if (v == null || v === '' || !isFinite(Number(v))) return null;
  const n = Number(v);
  return n <= 1 ? n * 100 : n;
}
function matchupTendencyLine(team){
  const s = styleForTeam(team) || {};
  const d = downSplitForTeam(team) || {};
  const pass = matchupPctValue(firstStyleValue(s, ['pass_rate']));
  const rush = matchupPctValue(firstStyleValue(s, ['rush_rate']));
  const stdRush = matchupPctValue(firstStyleValue(d, ['standard_down_rush_rate']));
  const passDownPass = matchupPctValue(firstStyleValue(d, ['passing_down_pass_rate']));
  const parts = [];
  if (pass != null) parts.push(`Pass ${Math.round(pass)}%`);
  if (rush != null) parts.push(`Rush ${Math.round(rush)}%`);
  if (stdRush != null) parts.push(`Std Rush ${Math.round(stdRush)}%`);
  if (passDownPass != null) parts.push(`Pass Down Pass ${Math.round(passDownPass)}%`);
  return parts.join(' · ');
}
function matchupComparisonStripForSide(offTeam, defTeam){
  const o = styleForTeam(offTeam) || {};
  const d = styleForTeam(defTeam) || {};
  const ds = downSplitForTeam(offTeam) || {};

  const offEff = firstStyleValue(o, ['offense_score','off_eff_score','offensive_success rate_score']);
  const defSucc = firstStyleValue(d, ['defense_score','def_eff_score','defensive_success rate_score']);
  const offExpl = firstStyleValue(o, ['explosive_score','explosiveness_score']);
  const defExpl = firstStyleValue(d, ['expl_prevent_score','def_explosive_score','explosive_defense_score','explosive_prevention_score']);
  const havocAvoid = firstStyleValue(o, ['havoc_risk_score','havoc_avoid_score','havoc_avoidance_score']);
  const havocCreate = firstStyleValue(d, ['havoc_creation_score','pressure_score','havoc_create_score']);
  const stdRush = matchupPctValue(firstStyleValue(ds, ['standard_down_rush_rate']));
  const runDef = firstStyleValue(d, ['run_front_score','front_score']);

  return `<div class="matchup-compare-box">
    <div class="matchup-compare-head">
      <span>${escapeHtml(offTeam)} offense</span>
      <em>vs</em>
      <span>${escapeHtml(defTeam)} defense</span>
    </div>

    <div class="matchup-compare-grid">
      ${matchupCompareChip('Off Success', offEff, 'Succ Prev', defSucc, 'success rate', offTeam, defTeam)}
      ${matchupCompareChip('Expl', offExpl, 'Expl Prev', defExpl, 'big plays', offTeam, defTeam)}
      ${matchupCompareChip('Havoc Avd', havocAvoid, 'Havoc Cr', havocCreate, 'pressure', offTeam, defTeam)}
      ${matchupCompareChip('Std Rush', stdRush, 'Run Def', runDef, 'run fit', offTeam, defTeam)}
    </div>

    <div class="matchup-tendency-strip">
      <b>Tendencies</b>
      <span>${escapeHtml(matchupTendencyLine(offTeam) || 'No tendency data')}</span>
    </div>
  </div>`;
}

function matchupPanelForSide(r){
  if (!r) return '<div class="matchup-panel"><div class="muted">No matchup data loaded for this side yet.</div></div>';

  const team = r.team;
  const opp = r.opponent;

  return `<div>
    <div class="matchup-side-title">${teamLabel(team)} offense vs ${teamLabel(opp)} defense</div>
    ${styleProfileHtml(team)}
    ${matchupPriorityHtml(r)}
    <div class="matchup-grid matchup-position-grid">
      ${matchupPositionCard(
        'Passing Game / Skill vs Coverage',
        'QB + WR/TE production vs opponent pass defense',
        team, opp, r.pass_off_edge,
        'Performance uses CFBD production. Talent compares QB/WR/TE vs opponent DB/LB coverage ratings.',
        'QB_WR_TE_vs_Coverage', 'DB_LB_Coverage'
      )}
      ${matchupPositionCard(
        'Run Game / OL vs Front Seven',
        'RB + OL rushing profile vs opponent DL/LB front',
        team, opp, r.rush_off_edge,
        'Performance uses CFBD rushing/front metrics. Talent compares RB/OL vs opponent DL/LB front ratings.',
        'OL_Run_Game_vs_Front_Seven', 'DL_LB_Front_Seven'
      )}
      ${matchupPressureCard(team, opp, r.pass_protection_edge)}
      ${matchupPositionCard(
        'Explosive Plays',
        'Big-play creation vs explosive-play prevention',
        team, opp, r.explosive_edge,
        'Performance shows explosive-play path. Talent compares skill-position ratings vs opponent coverage ratings.',
        'Explosive_Skill_vs_Explosive_Defense', 'DB_LB_Coverage'
      )}
    </div>
    <div class="matchup-summary matchup-position-summary">${escapeHtml(matchupSideRead(r))}</div>
  </div>`;
}

function coachHalfRowsFor(key){
  return Array.isArray(DB[key]) ? DB[key] : [];
}
function coachHalfByTeam(teamName, type){
  const key = matchupNormName(teamName);
  const rows = type === '1h' ? coachHalfRowsFor('coach_1h_betting') : coachHalfRowsFor('coach_2h_betting');
  return rows.find(r => matchupNormName(r.team) === key) || null;
}
function coachEdgePctText(v){
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  return `${Math.round(Number(v) * 100)}%`;
}
function coachEdgeMarginText(v){
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  const n = Number(v);
  return `${n > 0 ? '+' : ''}${n.toFixed(1)}`;
}
function coachEdgeDiff(a, b, field){
  if (!a || !b || a[field] == null || b[field] == null) return null;
  const av = Number(a[field]), bv = Number(b[field]);
  if (!isFinite(av) || !isFinite(bv)) return null;
  return av - bv;
}
function coachEdgeChipCompact(label, awayTeam, homeTeam, awayRow, homeRow){
  const edge = coachEdgeDiff(awayRow, homeRow, 'ats_pct');
  if (edge == null) return `<span class="coach-edge-chip neutral"><b>${escapeHtml(label)}</b> No data</span>`;
  if (Math.abs(edge) < 0.005) return `<span class="coach-edge-chip neutral"><b>${escapeHtml(label)}</b> Even</span>`;
  const owner = edge > 0 ? awayTeam : homeTeam;
  const cls = edge > 0 ? 'away' : 'home';
  return `<span class="coach-edge-chip ${cls}"><b>${escapeHtml(label)}</b> ${escapeHtml(owner)} +${Math.abs(edge * 100).toFixed(1)}%</span>`;
}
function coachEdgeMini(team, row, prefix=''){
  if (!row) return `<div class="coach-mini-line"><span>${teamLabel(team)}</span><em>${escapeHtml(prefix)} No data</em></div>`;
  const games = row.ats_games || row.games || '';
  const coach = row.head_coach || row.current_coach || 'Coach';
  return `<div class="coach-mini-line">
    <span>${teamLabel(team)}</span>
    <em>${escapeHtml(prefix)} ${escapeHtml(coach)}</em>
    <strong>ATS ${coachEdgePctText(row.ats_pct)} ${row.ats_rank ? `#${row.ats_rank}` : ''}</strong>
    <small>${escapeHtml(row.ats_record || '')}${games ? ` · n=${games}` : ''} · Avg ${coachEdgeMarginText(row.avg_ats_margin)}</small>
  </div>`;
}
function matchupCoachEdgeHtml(g){
  const away = g.away_team;
  const home = g.home_team;

  const aFG = typeof coachForTeam === 'function' ? coachForTeam(away) : null;
  const hFG = typeof coachForTeam === 'function' ? coachForTeam(home) : null;
  const a1H = coachHalfByTeam(away, '1h');
  const h1H = coachHalfByTeam(home, '1h');
  const a2H = coachHalfByTeam(away, '2h');
  const h2H = coachHalfByTeam(home, '2h');

  if (!aFG && !hFG && !a1H && !h1H && !a2H && !h2H) return '';

  function rankText(row){
    return row && row.ats_rank ? `#${row.ats_rank}` : '—';
  }

  function rankClass(row){
    if (!row || !row.ats_rank || !isFinite(Number(row.ats_rank))) return 'rank-na';
    const r = Number(row.ats_rank);
    if (r <= 25) return 'rank-good';
    if (r <= 75) return 'rank-mid';
    return 'rank-bad';
  }

  function rankPair(label, a, h){
    return `<span class="coach-rank-chip">
      <b>${escapeHtml(label)}</b>
      <span class="coach-rank-team ${rankClass(a)}">${escapeHtml(away)} ${rankText(a)}</span>
      <span class="coach-rank-vs">vs</span>
      <span class="coach-rank-team ${rankClass(h)}">${escapeHtml(home)} ${rankText(h)}</span>
    </span>`;
  }

  return `<div class="coach-rank-strip">
    <div class="coach-rank-title">Coach ATS Ranks</div>
    <div class="coach-rank-chips">
      ${rankPair('FG', aFG, hFG)}
      ${rankPair('1H', a1H, h1H)}
      ${rankPair('2H', a2H, h2H)}
    </div>
  </div>`;
}


const teamcraftersPositionRows = Array.isArray(DB.teamcrafters_position_group_ratings) ? DB.teamcrafters_position_group_ratings : [];
const teamcraftersPositionsByTeam = Object.fromEntries(
  teamcraftersPositionRows.map(r => [matchupNormName(r.team), r])
);

function teamcraftersTeamKey(team){
  let s = matchupNormName(team);

  const aliases = {
    'central florida': 'ucf',
    'florida international': 'fiu',
    'connecticut': 'uconn',
    'massachusetts': 'umass',
    'ul monroe': 'ul monroe',
    'ulmonroe': 'ul monroe',
    'ole miss': 'ole miss',
    'southern miss': 'southern miss',
    'southern miss golden': 'southern miss',
    'north dakota state': 'north dakota state',
    'sacramento state': 'sacramento state',
    'sacramento state university': 'sacramento state',
    'sam houston': 'sam houston',
  };
  if (aliases[s]) return aliases[s];

  const mascotSuffixes = [
    'fighting irish','bobcats','sooners','cowboys','monarchs','rebels','ducks','beavers',
    'boilermakers','scarlet knights','mustangs','hornets','bearkats','aztecs','jaguars',
    'golden eagles','golden','cardinal','orange','horned frogs','volunteers','longhorns',
    'red raiders','rockets','trojans','green wave','golden hurricane','blazers','bruins',
    'warhawks','miners','runnin rebels','rebels','utes','commodores','cavaliers','hokies',
    'demon deacons','hilltoppers','badgers','cowboys','panthers','golden flashes'
  ];

  for (const suf of mascotSuffixes) {
    if (s.endsWith(' ' + suf)) {
      s = s.slice(0, -(suf.length + 1)).trim();
      break;
    }
  }

  if (aliases[s]) return aliases[s];
  return s;
}

const teamcraftersPositionsByTeam2 = Object.fromEntries(
  teamcraftersPositionRows.map(r => [teamcraftersTeamKey(r.team), r])
);

function teamcraftersPositionsForTeam(team){
  const key = teamcraftersTeamKey(team);
  return teamcraftersPositionsByTeam2[key] || teamcraftersPositionsByTeam[matchupNormName(team)] || null;
}
function positionRatingClass(v){
  if (v == null || v === '' || !isFinite(Number(v))) return 'pos-rating-na';
  const n = Number(v);
  if (n >= 85) return 'pos-rating-good';
  if (n >= 75) return 'pos-rating-mid';
  return 'pos-rating-bad';
}
function positionRatingValue(v){
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  return String(Math.round(Number(v)));
}
function positionEdgeText(awayTeam, homeTeam, awayVal, homeVal){
  const av = awayVal == null || awayVal === '' || !isFinite(Number(awayVal)) ? null : Number(awayVal);
  const hv = homeVal == null || homeVal === '' || !isFinite(Number(homeVal)) ? null : Number(homeVal);
  if (av == null || hv == null) return '';
  const diff = av - hv;
  if (Math.abs(diff) < 0.5) return `<small class="pos-edge-even">Even</small>`;
  const owner = diff > 0 ? awayTeam : homeTeam;
  return `<small class="${diff > 0 ? 'pos-edge-away' : 'pos-edge-home'}">${escapeHtml(owner)} +${Math.abs(diff).toFixed(0)}</small>`;
}
function positionCompareChip(pos, key, awayTeam, homeTeam, awayRow, homeRow){
  const av = awayRow ? awayRow[key] : null;
  const hv = homeRow ? homeRow[key] : null;
  return `<div class="position-compare-chip">
    <div class="position-compare-label">${escapeHtml(pos)}</div>
    <div class="position-compare-pair">
      <span class="${positionRatingClass(av)}">${escapeHtml(awayTeam)} <b>${positionRatingValue(av)}</b></span>
      <em>vs</em>
      <span class="${positionRatingClass(hv)}">${escapeHtml(homeTeam)} <b>${positionRatingValue(hv)}</b></span>
    </div>
    ${positionEdgeText(awayTeam, homeTeam, av, hv)}
  </div>`;
}
function positionRatingsComparisonHtml(g){
  const away = g.away_team;
  const home = g.home_team;
  const awayRow = teamcraftersPositionsForTeam(away);
  const homeRow = teamcraftersPositionsForTeam(home);

  if (!awayRow && !homeRow) return '';

  const positions = [
    ['QB','qb'],
    ['RB','rb'],
    ['WR','wr'],
    ['TE','te'],
    ['OL','ol'],
    ['DL','dl'],
    ['LB','lb'],
    ['DB','db'],
    ['ST','kp'],
  ];

  return `<div class="position-ratings-box">
    <div class="position-ratings-title">
      <span>Position Ratings</span>
      <em>TeamCrafters CFB 26</em>
    </div>
    <div class="position-ratings-grid">
      ${positions.map(([label,key]) => positionCompareChip(label, key, away, home, awayRow, homeRow)).join('')}
    </div>
  </div>`;
}


function betTeamObj(team){
  return (DB.teams || []).find(t => matchupNormName(t.team) === matchupNormName(team)) || null;
}
function betGradeClass(v, invert=false){
  if (v == null || v === '' || !isFinite(Number(v))) return 'bet-na';
  const n = Number(v);
  if (!invert) {
    if (n >= 67) return 'bet-good';
    if (n >= 34) return 'bet-mid';
    return 'bet-bad';
  }
  if (n <= 25) return 'bet-good';
  if (n <= 75) return 'bet-mid';
  return 'bet-bad';
}
function betRating(v){
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  return Math.round(Number(v));
}
function betPct(v){
  if (v == null || v === '' || !isFinite(Number(v))) return '—';
  const n = Number(v);
  return `${Math.round(n <= 1 ? n * 100 : n)}%`;
}
function betCoachRowsFor(key){
  return Array.isArray(DB[key]) ? DB[key] : [];
}
function betCoach(team, key='coach_betting'){
  const tn = matchupNormName(team);
  return betCoachRowsFor(key).find(r => matchupNormName(r.team) === tn) || null;
}
function betCoachRank(team, key){
  const r = betCoach(team, key);
  return r && r.ats_rank ? Number(r.ats_rank) : null;
}
function betCoachRankChip(label, away, home, key){
  const ar = betCoachRank(away, key);
  const hr = betCoachRank(home, key);
  return `<span class="bet-chip bet-wide">
    <b>${escapeHtml(label)}</b>
    <span class="${betGradeClass(ar,true)}">${escapeHtml(away)} ${ar ? `#${ar}` : '—'}</span>
    <em>vs</em>
    <span class="${betGradeClass(hr,true)}">${escapeHtml(home)} ${hr ? `#${hr}` : '—'}</span>
  </span>`;
}
function betStyle(team){
  return styleForTeam(team) || {};
}
function betPos(team){
  return teamcraftersPositionsForTeam(team) || {};
}
function betPositionCompareChip(pos, key, away, home){
  const a = betPos(away)[key];
  const h = betPos(home)[key];
  const av = a == null ? null : Number(a);
  const hv = h == null ? null : Number(h);
  let edge = '';
  if (av != null && hv != null) {
    const d = av - hv;
    if (Math.abs(d) < .5) edge = '<small class="bet-neutral">Even</small>';
    else edge = `<small class="${d > 0 ? 'bet-away' : 'bet-home'}">${escapeHtml(d > 0 ? away : home)} +${Math.abs(d).toFixed(0)}</small>`;
  }
  return `<div class="bet-pos-chip">
    <div class="bet-pos-title">${escapeHtml(pos)}</div>
    <div>
      <span class="${betGradeClass(av)}">${escapeHtml(away)} ${betRating(av)}</span>
      <em>vs</em>
      <span class="${betGradeClass(hv)}">${escapeHtml(home)} ${betRating(hv)}</span>
    </div>
    ${edge}
  </div>`;
}
function betDaysBetween(a,b){
  if (!a || !b) return null;
  const da = new Date(a), db = new Date(b);
  if (isNaN(da.getTime()) || isNaN(db.getTime())) return null;
  return Math.round((db - da) / (1000*60*60*24));
}
function betTeamGames(team){
  return (DB.games || [])
    .filter(g => g.home_team === team || g.away_team === team)
    .slice()
    .sort((a,b) => String(a.date || '').localeCompare(String(b.date || '')));
}
function betOpponent(g, team){
  return g.home_team === team ? g.away_team : g.home_team;
}
function betIsRoad(g, team){
  return !g.neutral_site && g.away_team === team;
}
function betSituationalFlags(g, team){
  const games = betTeamGames(team);
  const idx = games.findIndex(x => String(matchupGameId(x)) === String(matchupGameId(g)));
  const prev = idx > 0 ? games[idx-1] : null;
  const next = idx >= 0 && idx < games.length - 1 ? games[idx+1] : null;

  const flags = [];

  if (prev && betIsRoad(prev, team) && betIsRoad(g, team)) {
    flags.push({label:'B2B Road', cls:'warn'});
  }

  const rest = prev ? betDaysBetween(prev.date, g.date) : null;
  if (rest != null && rest >= 10) flags.push({label:'Off Bye', cls:'good'});
  if (rest != null && rest <= 5) flags.push({label:'Short Rest', cls:'bad'});

  if (next) {
    const opp = betOpponent(next, team);
    const oppObj = betTeamObj(opp);
    const rivalry = (
      (team === 'Ohio State' && opp === 'Michigan') ||
      (team === 'Michigan' && opp === 'Ohio State')
    );
    if (rivalry || (oppObj && Number(oppObj.rank) <= 15)) {
      flags.push({label:`Lookahead: ${opp}`, cls:'warn'});
    }
  }

  return flags;
}
function betSituationalHtml(g, away, home){
  function side(team){
    const flags = betSituationalFlags(g, team);
    if (!flags.length) return `<span class="bet-chip"><b>${escapeHtml(team)}</b> clean spot</span>`;
    return `<span class="bet-chip"><b>${escapeHtml(team)}</b> ${flags.map(f => `<em class="${f.cls}">${escapeHtml(f.label)}</em>`).join(' ')}</span>`;
  }
  return `<div class="bet-situational-row">${side(away)}${side(home)}</div>`;
}
function betPreLineScore(g, team){
  const opp = betOpponent(g, team);
  const t = betTeamObj(team), o = betTeamObj(opp);
  let score = 50;

  // Power/rating edge
  if (t && o && isFinite(Number(t.combo)) && isFinite(Number(o.combo))) {
    score += Math.max(-15, Math.min(15, (Number(t.combo) - Number(o.combo)) * .8));
  }

  // Projected margin side, no market line yet
  if (g.projected_margin_home != null) {
    const m = Number(g.projected_margin_home);
    const sideM = g.home_team === team ? m : -m;
    if (isFinite(sideM)) score += Math.max(-12, Math.min(12, sideM * 1.2));
  }

  // Coach full-game ATS edge
  const c = betCoachRank(team, 'coach_betting');
  const co = betCoachRank(opp, 'coach_betting');
  if (c && co) score += Math.max(-6, Math.min(6, (co - c) / 12));

  // Situational flags
  for (const f of betSituationalFlags(g, team)) {
    if (f.cls === 'good') score += 3;
    if (f.cls === 'bad') score -= 3;
    if (f.cls === 'warn') score -= 2;
  }

  return Math.round(Math.max(0, Math.min(100, score)));
}
function betScoreChip(g, team){
  const s = betPreLineScore(g, team);
  const cls = s >= 67 ? 'bet-good' : s >= 45 ? 'bet-mid' : 'bet-bad';
  return `<span class="bet-score-chip ${cls}"><b>${escapeHtml(team)}</b> ${s}</span>`;
}

function betFactorClass(v){
  if (v == null || v === '' || !isFinite(Number(v))) return 'factor-neutral';
  const n = Number(v);
  if (n >= 67) return 'factor-good';
  if (n >= 45) return 'factor-mid';
  return 'factor-bad';
}
function betFactorPill(rank, label, team, value, note=''){
  return `<div class="bet-factor-pill ${betFactorClass(value)}">
    <span class="factor-rank">${rank}</span>
    <div>
      <b>${escapeHtml(label)}</b>
      <strong>${escapeHtml(team)} ${Math.round(Number(value))}</strong>
      ${note ? `<small>${escapeHtml(note)}</small>` : ''}
    </div>
  </div>`;
}
function betTopFactors(g){
  const away = g.away_team;
  const home = g.home_team;
  const factors = [];

  const awayScore = betPreLineScore(g, away);
  const homeScore = betPreLineScore(g, home);
  factors.push({
    label:'Setup score',
    team: awayScore >= homeScore ? away : home,
    value: Math.max(awayScore, homeScore),
    note:`${away} ${awayScore} vs ${home} ${homeScore}`
  });

  const a = betTeamObj(away), h = betTeamObj(home);
  if (a && h && a.rank && h.rank) {
    const better = Number(a.rank) < Number(h.rank) ? away : home;
    const val = 100 - Math.min(99, Math.abs(Number(a.rank) - Number(h.rank)));
    factors.push({
      label:'Overall rating gap',
      team: better,
      value: val,
      note:`#${a.rank} vs #${h.rank}`
    });
  }

  const aFG = betCoachRank(away, 'coach_betting');
  const hFG = betCoachRank(home, 'coach_betting');
  if (aFG && hFG) {
    const better = aFG < hFG ? away : home;
    const val = Math.min(100, 50 + Math.abs(aFG - hFG));
    factors.push({
      label:'Coach ATS',
      team: better,
      value: val,
      note:`FG rank #${aFG} vs #${hFG}`
    });
  }

  const awayFlags = betSituationalFlags(g, away);
  const homeFlags = betSituationalFlags(g, home);
  if (awayFlags.length || homeFlags.length) {
    const badAway = awayFlags.filter(f => f.cls === 'bad' || f.cls === 'warn').length;
    const badHome = homeFlags.filter(f => f.cls === 'bad' || f.cls === 'warn').length;
    const goodAway = awayFlags.filter(f => f.cls === 'good').length;
    const goodHome = homeFlags.filter(f => f.cls === 'good').length;
    const awayNet = goodAway - badAway;
    const homeNet = goodHome - badHome;
    const better = awayNet >= homeNet ? away : home;
    const val = 55 + Math.min(25, Math.abs(awayNet - homeNet) * 10);
    factors.push({
      label:'Schedule spot',
      team: better,
      value: val,
      note:`${away}: ${awayFlags.map(f=>f.label).join(', ') || 'clean'} | ${home}: ${homeFlags.map(f=>f.label).join(', ') || 'clean'}`
    });
  }

  // Position rating edge: sum available TeamCrafters raw position gaps.
  const aPos = teamcraftersPositionsForTeam(away) || {};
  const hPos = teamcraftersPositionsForTeam(home) || {};
  const keys = ['qb','rb','wr','te','ol','dl','lb','db','kp'];
  let posSum = 0, posN = 0;
  keys.forEach(k => {
    const av = aPos[k], hv = hPos[k];
    if (av != null && hv != null && isFinite(Number(av)) && isFinite(Number(hv))) {
      posSum += Number(av) - Number(hv);
      posN += 1;
    }
  });
  if (posN) {
    const avg = posSum / posN;
    const better = avg >= 0 ? away : home;
    const val = Math.min(100, 50 + Math.abs(avg) * 6);
    factors.push({
      label:'Position ratings',
      team: better,
      value: val,
      note:`avg position edge ${avg >= 0 ? '+' : ''}${avg.toFixed(1)}`
    });
  }

  return factors
    .filter(f => f.value != null && isFinite(Number(f.value)))
    .sort((x,y) => Number(y.value) - Number(x.value))
    .slice(0,4);
}
function betTopFactorsHtml(g){ return ''; }


function factorStrengthIcon(score){
  if (score == null || score === '' || !isFinite(Number(score))) return '—';
  const n = Number(score);
  if (n >= 82) return '✓✓✓';
  if (n >= 67) return '✓✓';
  if (n >= 52) return '✓';
  if (n <= 35) return '⚠';
  return '•';
}
function factorStrengthClass(score){
  if (score == null || score === '' || !isFinite(Number(score))) return 'setup-neutral';
  const n = Number(score);
  if (n >= 67) return 'setup-good';
  if (n >= 45) return 'setup-mid';
  return 'setup-bad';
}
function setupFactorRow(label, team, score, note='', detail=''){
  const cls = factorStrengthClass(score);
  const icon = factorStrengthIcon(score);
  const scoreText = score == null || score === '' || !isFinite(Number(score)) ? '—' : Math.round(Number(score));
  return `<div class="setup-factor-row ${cls}">
    <div class="setup-factor-icon">${escapeHtml(icon)}</div>
    <div class="setup-factor-main">
      <div class="setup-factor-top">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(team || '')} ${scoreText}</strong>
      </div>
      ${note ? `<div class="setup-factor-note">${escapeHtml(note)}</div>` : ''}
      ${detail ? `<div class="setup-factor-detail">${escapeHtml(detail)}</div>` : ''}
    </div>
  </div>`;
}
function setupScoreSummary(g){
  const away = g.away_team;
  const home = g.home_team;
  const awayScore = betPreLineScore(g, away);
  const homeScore = betPreLineScore(g, home);
  const leader = awayScore >= homeScore ? away : home;
  const diff = Math.abs(awayScore - homeScore);
  const confidence = diff >= 25 ? 'strong lean' : diff >= 12 ? 'lean' : 'thin/no clear lean';

  return `<div class="setup-score-head">
    <div>
      <div class="setup-score-title">Pre-Line Setup Score</div>
      <div class="setup-score-sub">Does this profile look bettable before a market line? Spread edge becomes primary once odds exist.</div>
    </div>
    <div class="setup-score-pills">
      <span class="${factorStrengthClass(awayScore)}"><b>${escapeHtml(away)}</b> ${awayScore}</span>
      <span class="${factorStrengthClass(homeScore)}"><b>${escapeHtml(home)}</b> ${homeScore}</span>
      <em>${escapeHtml(leader)} · ${escapeHtml(confidence)}</em>
    </div>
  </div>`;
}
function setupFactors(g){
  const away = g.away_team;
  const home = g.home_team;
  const factors = [];

  const awayScore = betPreLineScore(g, away);
  const homeScore = betPreLineScore(g, home);
  factors.push({
    label:'Setup score',
    team: awayScore >= homeScore ? away : home,
    score: Math.max(awayScore, homeScore),
    note:`${away} ${awayScore} vs ${home} ${homeScore}`,
    detail:'No market line included yet.'
  });

  const a = betTeamObj(away), h = betTeamObj(home);
  if (a && h && a.rank && h.rank) {
    const better = Number(a.rank) < Number(h.rank) ? away : home;
    const rankDiff = Math.abs(Number(a.rank) - Number(h.rank));
    const score = Math.min(100, 50 + rankDiff);
    factors.push({
      label:'Power / overall rank',
      team: better,
      score,
      note:`${away} #${a.rank} vs ${home} #${h.rank}`,
      detail:'Baseline team-strength edge.'
    });
  }

  const awayStyle = styleForTeam(away) || {};
  const homeStyle = styleForTeam(home) || {};
  const effAway = firstStyleValue(awayStyle, ['offense_score']);
  const defHome = firstStyleValue(homeStyle, ['defense_score']);
  const effHome = firstStyleValue(homeStyle, ['offense_score']);
  const defAway = firstStyleValue(awayStyle, ['defense_score']);

  if (effAway != null && defHome != null) {
    const edge = Number(effAway) - Number(defHome);
    const owner = edge >= 0 ? away : home;
    factors.push({
      label:'Success Rate matchup',
      team: owner,
      score: Math.min(100, 50 + Math.abs(edge)),
      note:`${away} Off Success ${Math.round(effAway)} vs ${home} Success Prevent ${Math.round(defHome)}`,
      detail:`Edge ${owner} +${Math.abs(edge).toFixed(0)}`
    });
  }

  if (effHome != null && defAway != null) {
    const edge = Number(effHome) - Number(defAway);
    const owner = edge >= 0 ? home : away;
    factors.push({
      label:'Success Rate counter',
      team: owner,
      score: Math.min(100, 50 + Math.abs(edge)),
      note:`${home} Off Success ${Math.round(effHome)} vs ${away} Success Prevent ${Math.round(defAway)}`,
      detail:`Edge ${owner} +${Math.abs(edge).toFixed(0)}`
    });
  }

  const aPos = teamcraftersPositionsForTeam(away) || {};
  const hPos = teamcraftersPositionsForTeam(home) || {};
  const keys = ['qb','rb','wr','te','ol','dl','lb','db','kp'];
  let posSum = 0, posN = 0;
  keys.forEach(k => {
    const av = aPos[k], hv = hPos[k];
    if (av != null && hv != null && isFinite(Number(av)) && isFinite(Number(hv))) {
      posSum += Number(av) - Number(hv);
      posN += 1;
    }
  });
  if (posN) {
    const avg = posSum / posN;
    const better = avg >= 0 ? away : home;
    factors.push({
      label:'Position talent',
      team: better,
      score: Math.min(100, 50 + Math.abs(avg) * 6),
      note:`Average position rating edge ${avg >= 0 ? '+' : ''}${avg.toFixed(1)}`,
      detail:'TeamCrafters CFB 26 position groups.'
    });
  }

  const aFG = betCoachRank(away, 'coach_betting');
  const hFG = betCoachRank(home, 'coach_betting');
  if (aFG && hFG) {
    const better = aFG < hFG ? away : home;
    const rankEdge = Math.abs(aFG - hFG);
    factors.push({
      label:'Coach ATS',
      team: better,
      score: Math.min(100, 50 + rankEdge),
      note:`FG ATS rank ${away} #${aFG} vs ${home} #${hFG}`,
      detail:'Historical full-game coach ATS rank.'
    });
  }

  const awayFlags = betSituationalFlags(g, away);
  const homeFlags = betSituationalFlags(g, home);
  if (awayFlags.length || homeFlags.length) {
    const awayBad = awayFlags.filter(f => f.cls === 'bad' || f.cls === 'warn').length;
    const homeBad = homeFlags.filter(f => f.cls === 'bad' || f.cls === 'warn').length;
    const awayGood = awayFlags.filter(f => f.cls === 'good').length;
    const homeGood = homeFlags.filter(f => f.cls === 'good').length;
    const awayNet = awayGood - awayBad;
    const homeNet = homeGood - homeBad;
    const better = awayNet >= homeNet ? away : home;
    factors.push({
      label:'Schedule spot',
      team: better,
      score: 55 + Math.min(30, Math.abs(awayNet - homeNet) * 12),
      note:`${away}: ${awayFlags.map(f=>f.label).join(', ') || 'clean'} | ${home}: ${homeFlags.map(f=>f.label).join(', ') || 'clean'}`,
      detail:'Bye, travel, road streak, lookahead.'
    });
  }

  return factors
    .filter(f => f.score != null && isFinite(Number(f.score)))
    .sort((x,y) => Number(y.score) - Number(x.score))
    .slice(0,6);
}
function setupFactorsHtml(g){
  const factors = setupFactors(g);
  return `<div class="setup-box">
    ${setupScoreSummary(g)}
    <div class="setup-factor-list">
      ${factors.map(f => setupFactorRow(f.label, f.team, f.score, f.note, f.detail)).join('')}
    </div>
  </div>`;
}

function bettingSnapshotHtml(g){
  const away = g.away_team;
  const home = g.home_team;
  const a = betTeamObj(away), h = betTeamObj(home);
  const as = betStyle(away), hs = betStyle(home);

  return `<div class="bet-snapshot-box">
    <div class="bet-snapshot-title">
      <span>Pre-Line Betting Snapshot</span>
      <em>0–100 score excludes market line; spread edge comes later when odds exist</em>
    </div>

    <div class="bet-score-row">
      ${betScoreChip(g, away)}
      ${betScoreChip(g, home)}
    </div>

    <div class="bet-main-grid">
      <div class="bet-mini-panel">
        <div class="bet-mini-title">Core Ratings</div>
        <div class="bet-chip-row">
          <span class="bet-chip"><b>Overall</b> ${escapeHtml(away)} #${a ? a.rank : '—'} <em>vs</em> ${escapeHtml(home)} #${h ? h.rank : '—'}</span>
          <span class="bet-chip"><b>Off Success</b> ${escapeHtml(away)} ${betRating(firstStyleValue(as, ['offense_score']))} <em>vs</em> ${escapeHtml(home)} ${betRating(firstStyleValue(hs, ['offense_score']))}</span>
          <span class="bet-chip"><b>Success Prevent</b> ${escapeHtml(away)} ${betRating(firstStyleValue(as, ['defense_score']))} <em>vs</em> ${escapeHtml(home)} ${betRating(firstStyleValue(hs, ['defense_score']))}</span>
        </div>
      </div>

    </div>


    <div class="bet-mini-panel">
      <div class="bet-mini-title">Situational Flags</div>
      ${betSituationalHtml(g, away, home)}
    </div>
  </div>`;
}


function teamContextKey(name){
  let s = matchupNormName(String(name || '').replace(/\s*\([^)]*\)\s*$/,''));
  const aliases = {
    'ohio st': 'ohio state',
    'oregon ducks': 'oregon',
    'ohio state buckeyes': 'ohio state',
    'penn st': 'penn state',
    'oklahoma st': 'oklahoma state',
    'app state': 'appalachian state',
    'arizona st': 'arizona state',
    'boise st': 'boise state',
    'florida st': 'florida state',
    'fresno st': 'fresno state',
    'iowa st': 'iowa state',
    'kansas st': 'kansas state',
    'michigan st': 'michigan state',
    'mississippi st': 'mississippi state',
    'nc state': 'nc state',
    'new mexico st': 'new mexico state',
    'oregon st': 'oregon state',
    'san diego st': 'san diego state',
    'san jose st': 'san jose state',
    'utah st': 'utah state',
    'washington st': 'washington state',
    'western kentucky': 'western kentucky',

    'app state': 'appalachian state',
    'appalachian st': 'appalachian state',
    'arizona st': 'arizona state',
    'arkansas st': 'arkansas state',
    'boise st': 'boise state',
    'c michigan': 'central michigan',
    'e michigan': 'eastern michigan',
    'fiu': 'florida international',
    'florida atlantic': 'florida atlantic',
    'ga tech': 'georgia tech',
    'georgia tech': 'georgia tech',
    'k state': 'kansas state',
    'michigan st': 'michigan state',
    'miami fl': 'miami-fl',
    'miami oh': 'miami-oh',
    'mississippi st': 'mississippi state',
    'n illinois': 'northern illinois',
    'nc state': 'nc state',
    'oklahoma st': 'oklahoma state',
    'ok state': 'oklahoma state',
    'ole miss': 'ole miss',
    's carolina': 'south carolina',
    'san jose st': 'san jose state',
    'southern miss': 'southern miss',
    'texas st': 'texas state',
    'uconn': 'connecticut',
    'umass': 'massachusetts',
    'utep': 'utep',
    'utsa': 'utsa',
    'w kentucky': 'western kentucky',
    'w michigan': 'western michigan'
  };
  return aliases[s] || s;
}
const teamContextRows = Array.isArray(DB.team_context_ratings) ? DB.team_context_ratings : [];
const teamContextByTeam = Object.fromEntries(teamContextRows.map(r => [teamContextKey(r.team), r]));

function teamContextFor(team){
  return teamContextByTeam[teamContextKey(team)] || null;
}
function contextRankClass(rank){
  if (rank == null || rank === '' || !isFinite(Number(rank))) return 'ctx-na';
  const r = Number(rank);
  if (r <= 35) return 'ctx-good';
  if (r <= 90) return 'ctx-mid';
  return 'ctx-bad';
}
function luckClass(v){
  if (v == null || v === '' || !isFinite(Number(v))) return 'ctx-na';
  const n = Number(v);
  // High positive luck = potential regression warning. Negative luck = possible bounce-back.
  if (n >= 1.0) return 'ctx-warn';
  if (n <= -1.0) return 'ctx-good';
  return 'ctx-mid';
}
function contextChip(team){
  const c = teamContextFor(team);
  if (!c) return `<span class="ctx-chip ctx-na"><b>${escapeHtml(team)}</b> no context</span>`;
  const cr = c.consistency_rank || null;
  const lr = c.luck_rank || null;
  const luck = c.luck_rating;
  return `<span class="ctx-chip">
    <b>${escapeHtml(team)}</b>
    <span class="${contextRankClass(cr)}">Cons #${cr || '—'}</span>
    <span class="${luckClass(luck)}">Luck ${luck == null ? '—' : (Number(luck)>0?'+':'') + Number(luck).toFixed(1)}</span>
  </span>`;
}
function matchupContextStripHtml(g){
  return `<div class="ctx-strip">
    <div class="ctx-title">Volatility / Luck</div>
    <div class="ctx-row">
      ${contextChip(g.away_team)}
      ${contextChip(g.home_team)}
    </div>
  </div>`;
}


function allTeamsByNameForSOS(){
  return Object.fromEntries((DB.teams || []).map(t => [matchupNormName(t.team), t]));
}
const sosTeamsByName = allTeamsByNameForSOS();

function sosTeam(team){
  return sosTeamsByName[matchupNormName(team)] || null;
}

function sosRankMaps(){
  const teams = (DB.teams || []).slice();

  const overall = teams
    .filter(t => t.rank != null)
    .sort((a,b) => Number(a.rank) - Number(b.rank));

  const off = teams
    .filter(t => t.sp_offense != null && isFinite(Number(t.sp_offense)))
    .sort((a,b) => Number(b.sp_offense) - Number(a.sp_offense));

  const def = teams
    .filter(t => t.sp_defense != null && isFinite(Number(t.sp_defense)))
    .sort((a,b) => Number(a.sp_defense) - Number(b.sp_defense));

  const out = {overall:{}, off:{}, def:{}};

  overall.forEach((t,i) => out.overall[matchupNormName(t.team)] = i + 1);
  off.forEach((t,i) => out.off[matchupNormName(t.team)] = i + 1);
  def.forEach((t,i) => out.def[matchupNormName(t.team)] = i + 1);

  return out;
}
const sosRanks = sosRankMaps();

function sosOpponent(g, team){
  return g.home_team === team ? g.away_team : g.home_team;
}

function sosGameDate(g){
  const d = new Date(g.date || g.cfbd_date || g.start_date || '');
  return isNaN(d.getTime()) ? null : d;
}

function sosPriorGames(team, currentGame){
  const curWeek = Number(currentGame.week);
  const curDate = sosGameDate(currentGame);

  return (DB.games || [])
    .filter(g => g.home_team === team || g.away_team === team)
    .filter(g => {
      if (String(matchupGameId(g)) === String(matchupGameId(currentGame))) return false;

      const gw = Number(g.week);
      if (isFinite(curWeek) && isFinite(gw)) return gw < curWeek;

      const gd = sosGameDate(g);
      if (curDate && gd) return gd < curDate;

      return false;
    })
    .sort((a,b) => Number(a.week || 0) - Number(b.week || 0));
}

function sosAvg(vals){
  const clean = vals.filter(v => v != null && isFinite(Number(v))).map(Number);
  if (!clean.length) return null;
  return clean.reduce((a,b) => a+b, 0) / clean.length;
}

function sosBestRank(vals){
  const clean = vals.filter(v => v != null && isFinite(Number(v))).map(Number);
  if (!clean.length) return null;
  return Math.min(...clean);
}

function sosRankClass(rank){
  if (rank == null || !isFinite(Number(rank))) return 'sos-na';
  const r = Number(rank);
  if (r <= 25) return 'sos-elite';
  if (r <= 60) return 'sos-good';
  if (r <= 95) return 'sos-mid';
  return 'sos-soft';
}

function sosRankText(rank){
  if (rank == null || !isFinite(Number(rank))) return '—';
  return `#${Math.round(Number(rank))}`;
}

function sosStepLabel(currentRank, avgRank, bestRank){
  if (currentRank == null || !isFinite(Number(currentRank))) return {label:'No rating', cls:'sos-na'};

  if (bestRank != null && Number(currentRank) < Number(bestRank)) {
    return {label:'Biggest test', cls:'sos-elite'};
  }

  if (avgRank == null || !isFinite(Number(avgRank))) {
    return {label:'No prior sample', cls:'sos-na'};
  }

  const diff = Number(avgRank) - Number(currentRank); // positive means current opponent is harder than average prior opponent
  if (diff >= 20) return {label:'Step up', cls:'sos-good'};
  if (diff <= -20) return {label:'Step down', cls:'sos-soft'};
  return {label:'Similar level', cls:'sos-mid'};
}

function sosContextForTeam(team, currentGame){
  const opp = sosOpponent(currentGame, team);
  const oppObj = sosTeam(opp);
  const oppKey = matchupNormName(opp);

  const prior = sosPriorGames(team, currentGame);
  const priorOpps = prior.map(g => sosOpponent(g, team));

  const priorOverall = priorOpps.map(o => sosRanks.overall[matchupNormName(o)]);
  const priorOppOff = priorOpps.map(o => sosRanks.off[matchupNormName(o)]);
  const priorOppDef = priorOpps.map(o => sosRanks.def[matchupNormName(o)]);

  const currentOverall = sosRanks.overall[oppKey];
  const currentOppOff = sosRanks.off[oppKey];
  const currentOppDef = sosRanks.def[oppKey];

  const avgOverall = sosAvg(priorOverall);
  const bestOverall = sosBestRank(priorOverall);

  const avgOppOff = sosAvg(priorOppOff);
  const bestOppOff = sosBestRank(priorOppOff);

  const avgOppDef = sosAvg(priorOppDef);
  const bestOppDef = sosBestRank(priorOppDef);

  return {
    team,
    opp,
    priorCount: prior.length,
    currentOverall,
    currentOppOff,
    currentOppDef,
    avgOverall,
    bestOverall,
    avgOppOff,
    bestOppOff,
    avgOppDef,
    bestOppDef,
    overallStep: sosStepLabel(currentOverall, avgOverall, bestOverall),
    offenseStep: sosStepLabel(currentOppDef, avgOppDef, bestOppDef),
    defenseStep: sosStepLabel(currentOppOff, avgOppOff, bestOppOff),
  };
}

function sosMetricChip(label, currentRank, avgRank, bestRank, step){
  return `<div class="sos-metric-chip">
    <div class="sos-metric-label">${escapeHtml(label)}</div>
    <div class="sos-current ${sosRankClass(currentRank)}">Now ${sosRankText(currentRank)}</div>
    <div class="sos-small">Avg ${sosRankText(avgRank)} · Max ${sosRankText(bestRank)}</div>
    <div class="sos-step ${step.cls}">${escapeHtml(step.label)}</div>
  </div>`;
}


function sosCompletedPriorGames(team, currentGame){
  return sosPriorGames(team, currentGame).filter(g =>
    g.cfbd_completed === true ||
    g.completed === true ||
    String(g.status || '').toLowerCase() === 'final' ||
    String(g.cfbd_status || '').toLowerCase() === 'completed'
  );
}
function sosGameTeamPoints(g, team){
  if (g.home_team === team) {
    const v = g.home_points ?? g.home_score ?? g.cfbd_home_points ?? g.home_final_points;
    return v == null || !isFinite(Number(v)) ? null : Number(v);
  }
  if (g.away_team === team) {
    const v = g.away_points ?? g.away_score ?? g.cfbd_away_points ?? g.away_final_points;
    return v == null || !isFinite(Number(v)) ? null : Number(v);
  }
  return null;
}
function sosGameOppPoints(g, team){
  if (g.home_team === team) {
    const v = g.away_points ?? g.away_score ?? g.cfbd_away_points ?? g.away_final_points;
    return v == null || !isFinite(Number(v)) ? null : Number(v);
  }
  if (g.away_team === team) {
    const v = g.home_points ?? g.home_score ?? g.cfbd_home_points ?? g.home_final_points;
    return v == null || !isFinite(Number(v)) ? null : Number(v);
  }
  return null;
}
function sosAtsResultForTeam(g, team){
  const raw = g.home_ats_result || g.home_game_ats_result || g.ats_result;
  if (!raw) return null;
  const r = String(raw).toUpperCase();
  if (!['W','L','P'].includes(r)) return null;
  if (team === g.home_team) return r;
  if (team === g.away_team) return r === 'W' ? 'L' : r === 'L' ? 'W' : 'P';
  return null;
}
function sosRankForOpponent(opp, type){
  const key = matchupNormName(opp);
  if (type === 'overall') return sosRanks.overall[key];
  if (type === 'offense') return sosRanks.off[key];
  if (type === 'defense') return sosRanks.def[key];
  return null;
}
function sosPerformanceVsCaliber(team, currentGame, type, maxRank){
  const games = sosCompletedPriorGames(team, currentGame).filter(g => {
    const opp = sosOpponent(g, team);
    const rank = sosRankForOpponent(opp, type);
    return rank != null && Number(rank) <= maxRank;
  });

  if (!games.length) return null;

  const pts = [], allowed = [];
  let atsW = 0, atsL = 0, atsP = 0;

  games.forEach(g => {
    const pf = sosGameTeamPoints(g, team);
    const pa = sosGameOppPoints(g, team);
    if (pf != null) pts.push(pf);
    if (pa != null) allowed.push(pa);

    const ats = sosAtsResultForTeam(g, team);
    if (ats === 'W') atsW++;
    if (ats === 'L') atsL++;
    if (ats === 'P') atsP++;
  });

  const avgPts = pts.length ? pts.reduce((a,b)=>a+b,0) / pts.length : null;
  const avgAllowed = allowed.length ? allowed.reduce((a,b)=>a+b,0) / allowed.length : null;

  return {games: games.length, avgPts, avgAllowed, atsW, atsL, atsP};
}
function sosCaliberLine(label, data){
  if (!data) return `<div class="sos-caliber-line"><span>${escapeHtml(label)}</span><b>—</b></div>`;
  const pts = data.avgPts == null ? '—' : data.avgPts.toFixed(1);
  const allowed = data.avgAllowed == null ? '—' : data.avgAllowed.toFixed(1);
  const atsGames = data.atsW + data.atsL + data.atsP;
  const ats = atsGames ? `${data.atsW}-${data.atsL}${data.atsP ? '-' + data.atsP : ''} ATS` : 'ATS —';
  return `<div class="sos-caliber-line"><span>${escapeHtml(label)}</span><b>${data.games}g · ${pts} PF · ${allowed} PA · ${ats}</b></div>`;
}
function sosCaliberPerformanceHtml(ctx){
  const g = ctx.currentGame;
  if (!g) return '';
  return `<div class="sos-caliber-box">
    <div class="sos-caliber-title">Performance vs Similar Caliber</div>
    ${sosCaliberLine('Top-25 overall', sosPerformanceVsCaliber(ctx.team, g, 'overall', 25))}
    ${sosCaliberLine('Top-40 offense faced', sosPerformanceVsCaliber(ctx.team, g, 'offense', 40))}
    ${sosCaliberLine('Top-40 defense faced', sosPerformanceVsCaliber(ctx.team, g, 'defense', 40))}
  </div>`;
}

function sosTeamContextCard(ctx){
  if (!ctx.priorCount) {
    return `<div class="sos-team-card">
      <div class="sos-team-title">${teamLabel(ctx.team)}</div>
      <div class="sos-caliber-placeholder"><b>Performance vs Similar Caliber</b><span>Top-25 overall — · Top-40 offense — · Top-40 defense —</span></div>
      <div class="sos-no-prior">No prior 2026 games before this matchup.</div>
      ${sosCaliberPerformanceHtml(ctx)}
      <div class="sos-metric-grid">
        ${sosMetricChip('Current Opp Overall', ctx.currentOverall, null, null, ctx.overallStep)}
        ${sosMetricChip('Offense vs Opp Def', ctx.currentOppDef, null, null, ctx.offenseStep)}
        ${sosMetricChip('Defense vs Opp Off', ctx.currentOppOff, null, null, ctx.defenseStep)}
      </div>
    </div>`;
  }

  return `<div class="sos-team-card">
    <div class="sos-team-title">${teamLabel(ctx.team)} <span>${ctx.priorCount} prior game${ctx.priorCount === 1 ? '' : 's'}</span></div>
    ${sosCaliberPerformanceHtml(ctx)}
    <div class="sos-metric-grid">
      ${sosMetricChip('Overall SOS', ctx.currentOverall, ctx.avgOverall, ctx.bestOverall, ctx.overallStep)}
      ${sosMetricChip('Offense test', ctx.currentOppDef, ctx.avgOppDef, ctx.bestOppDef, ctx.offenseStep)}
      ${sosMetricChip('Defense test', ctx.currentOppOff, ctx.avgOppOff, ctx.bestOppOff, ctx.defenseStep)}
    </div>
  </div>`;
}

function matchupSOSContextHtml(g){
  const awayCtx = sosContextForTeam(g.away_team, g);
  const homeCtx = sosContextForTeam(g.home_team, g);

  return `<div class="sos-context-box">
    <div class="sos-context-title">
      <span>Schedule Strength Context</span>
      <em>Prior 2026 opponents before this matchup</em>
    </div>
    <div class="sos-context-grid">
      ${sosTeamContextCard(awayCtx)}
      ${sosTeamContextCard(homeCtx)}
    </div>
  </div>`;
}


function cfbNum(v){
  if (v == null || v === '' || !isFinite(Number(v))) return null;
  return Number(v);
}
function cfbRankClass(rank){
  if (rank == null || rank === '' || !isFinite(Number(rank))) return 'cfb-rank-na';
  const r = Number(rank);
  if (r <= 35) return 'cfb-rank-good';
  if (r <= 85) return 'cfb-rank-mid';
  return 'cfb-rank-bad';
}
function cfbRankChip(rank){
  if (rank == null || rank === '' || !isFinite(Number(rank))) return `<span class="cfb-factor-rank cfb-rank-na">—</span>`;
  return `<span class="cfb-factor-rank ${cfbRankClass(rank)}">${Math.round(Number(rank))}</span>`;
}
function cfbFmt(v, kind='grade'){
  const n = cfbNum(v);
  if (n == null) return '—';
  if (kind === 'pct') return `${Math.round(n <= 1 ? n*100 : n)}%`;
  if (kind === 'decimal') return Math.abs(n) < 10 ? n.toFixed(2) : n.toFixed(1);
  if (kind === 'signed') return `${n > 0 ? '+' : ''}${n.toFixed(1)}`;
  return `${Math.round(n)}`;
}
function cfbTeamRank(team){
  const t = betTeamObj(team);
  return t && t.rank != null ? Number(t.rank) : null;
}
function cfbRatingValue(team, type){
  const t = betTeamObj(team) || {};
  if (type === 'overall') return firstStyleValue(t, ['combo','rating','overall_rating','sp_overall','sp_rating']);
  if (type === 'off') return firstStyleValue(t, ['sp_offense','off_rating','offense_rating']);
  if (type === 'def') return firstStyleValue(t, ['sp_defense','def_rating','defense_rating']);
  return null;
}
function cfbRatingRank(team, type){
  const t = betTeamObj(team) || {};
  if (type === 'overall') return cfbTeamRank(team);
  if (type === 'off') return Number(t.off_rank || t.offense_rank || t.sp_offense_rank || sosRanks?.off?.[matchupNormName(team)] || null) || null;
  if (type === 'def') return Number(t.def_rank || t.defense_rank || t.sp_defense_rank || sosRanks?.def?.[matchupNormName(team)] || null) || null;
  return null;
}
function cfbPowerValueBlock(team, value, rank, align='left'){
  return `<div class="cfb-power-team ${align === 'right' ? 'right' : ''}">${escapeHtml(team)} <span class="cfb-power-val">${cfbFmt(value,'decimal')}</span><span class="cfb-context-sub">#${rank || '—'}</span></div>`;
}
function cfbPowerRankEdge(leftTeam, rightTeam, leftRank, rightRank){
  return cfbRankEdgeBadge(leftTeam, rightTeam, leftRank, rightRank);
}
function cfbPowerCardOverall(away, home){
  const av = cfbRatingValue(away, 'overall'), hv = cfbRatingValue(home, 'overall');
  const ar = cfbRatingRank(away, 'overall'), hr = cfbRatingRank(home, 'overall');
  return `<div class="cfb-power-card">
    <div class="cfb-power-label">Overall Rating / Rank</div>
    <div class="cfb-power-row">
      ${cfbPowerValueBlock(away, av, ar)}
      ${cfbPowerRankEdge(away, home, ar, hr)}
      ${cfbPowerValueBlock(home, hv, hr, 'right')}
    </div>
  </div>`;
}
function cfbPowerCardOffVsDef(offTeam, defTeam){
  const ov = cfbRatingValue(offTeam, 'off'), dv = cfbRatingValue(defTeam, 'def');
  const or = cfbRatingRank(offTeam, 'off'), dr = cfbRatingRank(defTeam, 'def');
  return `<div class="cfb-power-card">
    <div class="cfb-power-label">${escapeHtml(offTeam)} Off vs ${escapeHtml(defTeam)} Def</div>
    <div class="cfb-power-row">
      ${cfbPowerValueBlock(offTeam, ov, or)}
      ${cfbPowerRankEdge(offTeam, defTeam, or, dr)}
      ${cfbPowerValueBlock(defTeam, dv, dr, 'right')}
    </div>
  </div>`;
}
function cfbPowerRatingsHtml(g){
  return `<div class="cfb-section">
    <div class="cfb-section-title"><span>Core Power Ratings</span><em>rating value + rank · offense vs opponent defense</em></div>
    <div class="cfb-power-grid">
      ${cfbPowerCardOverall(g.away_team, g.home_team)}
      ${cfbPowerCardOffVsDef(g.away_team, g.home_team)}
      ${cfbPowerCardOffVsDef(g.home_team, g.away_team)}
    </div>
  </div>`;
}
function cfbStyleMetric(team, metric, side){
  const s = styleForTeam(team) || {};
  const map = {
    ppa: side === 'off' ? ['ppa_score','ppa_per_play_score','off_ppa_score','offense_score'] : ['ppa_prevent_score','def_ppa_score','defense_score'],
    success: side === 'off' ? ['success_rate_score','off_success_score','offense_score'] : ['success_prevent_score','def_success_score','defense_score'],
    explosive: side === 'off' ? ['explosive_score','explosiveness_score'] : ['expl_prevent_score','explosive_prevention_score','def_explosive_score'],
    // Fallbacks keep these populated until true finishing-drive and field-position imports are added.
    finishing: side === 'off' ? ['finishing_drives_score','finishing_score','finish_score','red_zone_score','offense_score'] : ['finishing_prevent_score','finish_prevent_score','red_zone_def_score','defense_score'],
    field: side === 'off' ? ['field_position_score','field_pos_score','starting_field_position_score','tempo_score','offense_score'] : ['field_position_prevent_score','field_pos_def_score','starting_field_position_def_score','defense_score'],
    // Offense side = havoc avoided / ball security. Defense side = havoc created / disruption.
    havoc: side === 'off' ? ['havoc_avoid_score','havoc_allowed_score','ball_security_score','turnover_avoidance_score','offense_score'] : ['havoc_creation_score','havoc_rate_score','pressure_score','defense_score'],
    front7havoc: side === 'off' ? ['front7_havoc_avoid_score','front_seven_havoc_avoid_score','rush_stuff_avoid_score','havoc_avoid_score','offense_score'] : ['front7_havoc_score','front_seven_havoc_score','line_havoc_score','pressure_score','defense_score'],
    dbhavoc: side === 'off' ? ['db_havoc_avoid_score','passing_havoc_avoid_score','sack_int_avoid_score','havoc_avoid_score','offense_score'] : ['db_havoc_score','secondary_havoc_score','pass_havoc_score','pressure_score','defense_score']
  };
  return firstStyleValue(s, map[metric] || []);
}
function cfbMetricRank(team, metric, side){
  const val = cfbStyleMetric(team, metric, side);
  return val == null ? null : Math.max(1, Math.min(138, Math.round(139 - Number(val) * 1.38)));
}
function cfbCheckCountByRankGap(gap){
  const n = Math.abs(Number(gap));
  if (!isFinite(n) || n < 8) return 0;
  if (n < 25) return 1;
  if (n < 55) return 2;
  return 3;
}
function cfbCheckCountByValueGap(gap, small=0.5, medium=1.25, large=2.25){
  const n = Math.abs(Number(gap));
  if (!isFinite(n) || n < small) return 0;
  if (n < medium) return 1;
  if (n < large) return 2;
  return 3;
}
function cfbEdgeBadge(owner, count, side='away'){
  if (!owner || !count) return `<span class="cfb-edge-pill even">—</span>`;
  const cls = side === 'home' ? 'edge-home' : 'edge-away';
  return `<span class="cfb-edge-pill ${cls}">${escapeHtml(owner)} <span class="cfb-checks">${'✓'.repeat(Math.max(1, Math.min(3, count)))}</span></span>`;
}
function cfbRankEdgeBadge(leftTeam, rightTeam, leftRank, rightRank){
  if (leftRank == null || rightRank == null) return `<span class="cfb-edge-pill even">—</span>`;
  const gap = Number(rightRank) - Number(leftRank); // positive means left has better/lower rank
  const count = cfbCheckCountByRankGap(gap);
  if (!count) return `<span class="cfb-edge-pill even">—</span>`;
  return gap > 0 ? cfbEdgeBadge(leftTeam, count, 'away') : cfbEdgeBadge(rightTeam, count, 'home');
}
function cfbFactorRow(label, metric, offTeam, defTeam){
  const or = cfbMetricRank(offTeam, metric, 'off');
  const dr = cfbMetricRank(defTeam, metric, 'def');

  let offEdge = `<span class="cfb-edge-pill even">—</span>`;
  let defEdge = `<span class="cfb-edge-pill even">—</span>`;

  if (or != null && dr != null) {
    const gap = Number(dr) - Number(or); // positive = offense rank is better/lower
    const count = cfbCheckCountByRankGap(gap);

    if (count && gap > 0) {
      offEdge = cfbEdgeBadge(offTeam, count, 'away');
    } else if (count && gap < 0) {
      defEdge = cfbEdgeBadge(defTeam, count, 'home');
    }
  }

  return `<tr>
    <td class="cfb-edge-cell cfb-off-edge-col">${offEdge}</td>
    <td class="cfb-left">${cfbRankChip(or)}</td>
    <td class="cfb-factor-name">${escapeHtml(label)}</td>
    <td class="cfb-right">${cfbRankChip(dr)}</td>
    <td class="cfb-edge-cell cfb-def-edge-col">${defEdge}</td>
  </tr>`;
}

function cfbFourFactorsSideHtml(offTeam, defTeam){
  return `<div class="cfb-side-card">
    <div class="cfb-side-head"><span>${escapeHtml(offTeam)} OFF</span><em>vs</em><span>${escapeHtml(defTeam)} DEF</span></div>
    <table class="cfb-factor-table cfb-split-edge-restored">
      <colgroup>
        <col style="width:22%">
        <col style="width:12%">
        <col style="width:30%">
        <col style="width:12%">
        <col style="width:24%">
      </colgroup>
      <thead>
        <tr>
          <th>Offense Edge<br><span class="cfb-edge-note">- = no edge</span></th>
          <th>Off Rk</th>
          <th>Metric</th>
          <th>Def Rk</th>
          <th>Defense Edge<br><span class="cfb-edge-note">- = no edge</span></th>
        </tr>
      </thead>
      <tbody>
        ${cfbFactorRow('Success Rate','success',offTeam,defTeam)}
        ${cfbFactorRow('Explosiveness','explosive',offTeam,defTeam)}
        ${cfbFactorRow('Finishing Drives','finishing',offTeam,defTeam)}
        ${cfbFactorRow('Field Position','field',offTeam,defTeam)}
        ${cfbFactorRow('Havoc Rate','havoc',offTeam,defTeam)}
      </tbody>
    </table>
  </div>`;
}

function cfbFourFactorsHtml(g){
  return `<div class="cfb-section">
    <div class="cfb-section-title"><span>Five Factors</span><em>ranks out of 138 · offense vs opponent defense</em></div>
    <div class="cfb-four-grid">
      ${cfbFourFactorsSideHtml(g.away_team, g.home_team)}
      ${cfbFourFactorsSideHtml(g.home_team, g.away_team)}
    </div>
  </div>`;
}
function cfbGameHeaderHtml(g){
  const spread = g.projected_margin_home == null || !isFinite(Number(g.projected_margin_home)) ? 'Proj spread —' : `${Number(g.projected_margin_home) > 0 ? g.home_team : g.away_team} -${Math.abs(Number(g.projected_margin_home)).toFixed(1)}`;
  const total = g.projected_total == null || !isFinite(Number(g.projected_total)) ? 'Total —' : `Total ${fmtProjectedTotalSafe(g.projected_total)}`;
  const market = [g.market_spread || g.sgo_spread || g.spread, g.market_total || g.sgo_total || g.total].filter(Boolean).join(' · ');
  return `<div class="cfb-matchup-header">
    <div class="cfb-team-head"><span class="cfb-team-logo">${advTeamLogo(g.away_team)}</span><div><div class="cfb-team-name">${escapeHtml(g.away_team)}</div><div class="cfb-team-sub">Away</div></div></div>
    <div class="cfb-game-center"><div class="cfb-game-title">Advanced matchup preview</div><div class="cfb-game-proj">${escapeHtml(spread)} · ${escapeHtml(total)}</div><div class="cfb-game-market">${market ? 'Market: '+escapeHtml(market) : 'Market line not loaded yet'}</div></div>
    <div class="cfb-team-head home"><div><div class="cfb-team-name">${escapeHtml(g.home_team)}</div><div class="cfb-team-sub">Home</div></div><span class="cfb-team-logo">${advTeamLogo(g.home_team)}</span></div>
  </div>`;
}
function cfbContextEdgeValue(away, home, awayVal, homeVal, small=0.5, medium=1.25, large=2.25){
  if (awayVal == null || homeVal == null || !isFinite(Number(awayVal)) || !isFinite(Number(homeVal))) return `<span class="cfb-edge-pill even">—</span>`;
  const diff = Number(awayVal) - Number(homeVal);
  const count = cfbCheckCountByValueGap(diff, small, medium, large);
  if (!count) return `<span class="cfb-edge-pill even">—</span>`;
  return diff > 0 ? cfbEdgeBadge(away, count, 'away') : cfbEdgeBadge(home, count, 'home');
}
function cfbContextRow(cat, awayVal, homeVal, edgeHtml){
  return `<tr><td class="cfb-context-cat">${escapeHtml(cat)}</td><td>${awayVal}</td><td>${homeVal}</td><td class="cfb-edge-cell">${edgeHtml}</td></tr>`;
}
function cfbCoachValue(team, key){
  const r = typeof betCoach === 'function' ? betCoach(team, key) : null;
  if (!r) return '—';
  const rank = r.ats_rank ? `#${r.ats_rank}` : '#—';
  const rec = r.ats_record || 'ATS —';
  const margin = r.avg_ats_margin == null ? 'ATS +/- —' : `ATS +/- ${coachEdgeMarginText(r.avg_ats_margin)}`;
  return `${rank} <span class="cfb-context-sub">${escapeHtml(rec)} · ${escapeHtml(margin)}</span>`;
}
function cfbTeamAtsResultForPeriod(g, team, period='fg'){
  const prefixes = period === '1h' ? ['1h','first_half','h1'] : period === '2h' ? ['2h','second_half','h2'] : ['','full_game','fg','game'];
  for (const pref of prefixes){
    const sep = pref ? '_' : '';
    const raw = g[`home_${pref}${sep}ats_result`] ?? g[`home_${pref}${sep}game_ats_result`] ?? g[`home_${pref}${sep}cover_result`] ?? (period==='fg' ? (g.home_ats_result || g.home_game_ats_result || g.ats_result) : null);
    if (!raw) continue;
    const r = String(raw).toUpperCase();
    if (!['W','L','P'].includes(r)) continue;
    if (team === g.home_team) return r;
    if (team === g.away_team) return r === 'W' ? 'L' : r === 'L' ? 'W' : 'P';
  }
  return null;
}
function cfbTeamAtsMarginForPeriod(g, team, period='fg'){
  const homeKeys = period === '1h'
    ? ['home_1h_ats_margin','home_first_half_ats_margin','home_h1_ats_margin','home_1h_cover_margin']
    : period === '2h'
      ? ['home_2h_ats_margin','home_second_half_ats_margin','home_h2_ats_margin','home_2h_cover_margin']
      : ['home_ats_margin','home_game_ats_margin','home_cover_margin','ats_margin'];
  for (const k of homeKeys){
    if (g[k] != null && isFinite(Number(g[k]))) {
      const v = Number(g[k]);
      return team === g.home_team ? v : team === g.away_team ? -v : null;
    }
  }
  return null;
}
function cfbCurrentAtsSummary(team, currentGame, period='fg'){
  const games = typeof sosCompletedPriorGames === 'function' ? sosCompletedPriorGames(team, currentGame) : [];
  let w=0,l=0,push=0, margins=[];
  games.forEach(g => {
    const r = cfbTeamAtsResultForPeriod(g, team, period);
    if (r === 'W') w++; else if (r === 'L') l++; else if (r === 'P') push++;
    const m = cfbTeamAtsMarginForPeriod(g, team, period);
    if (m != null && isFinite(Number(m))) margins.push(Number(m));
  });
  const n = w+l+push;
  if (!n && !margins.length) return null;
  const avg = margins.length ? margins.reduce((a,b)=>a+b,0)/margins.length : null;
  return {w,l,p:push,n,avg};
}
function cfbCurrentAtsText(sum){
  if (!sum) return '—';
  const rec = `${sum.w}-${sum.l}${sum.p ? '-' + sum.p : ''}`;
  const avg = sum.avg == null ? 'margin —' : `margin ${coachEdgeMarginText(sum.avg)}`;
  return `${rec} <span class="cfb-context-sub">${avg}</span>`;
}
function cfbCurrentAtsEdge(away, home, aSum, hSum){
  const av = aSum && aSum.avg != null ? aSum.avg : null;
  const hv = hSum && hSum.avg != null ? hSum.avg : null;
  return cfbContextEdgeValue(away, home, av, hv, .75, 2.0, 4.0);
}
function cfbLuckRank(team){
  const ctx = teamContextFor(team) || {};
  const val = ctx.luck_rating;
  if (val == null || !isFinite(Number(val))) return null;
  const rows = (DB.teams || []).map(t => ({team:t.team, value:(teamContextFor(t.team)||{}).luck_rating})).filter(x => x.value != null && isFinite(Number(x.value)));
  rows.sort((a,b) => Number(b.value) - Number(a.value));
  const idx = rows.findIndex(x => matchupNormName(x.team) === matchupNormName(team));
  return idx >= 0 ? idx + 1 : null;
}
function cfbLuckText(team){
  const ctx = teamContextFor(team) || {};
  const v = ctx.luck_rating;
  const r = cfbLuckRank(team);
  if (v == null || !isFinite(Number(v))) return '—';
  const n = Number(v);
  const cls = n >= 1 ? 'neg' : n <= -1 ? 'pos' : '';
  return `<span class="${cls}">#${r || '—'} · ${cfbFmt(n,'signed')}</span><span class="cfb-context-sub">+ = lucky / - = unlucky</span>`;
}
function cfbLuckEdge(away, home){
  const av = (teamContextFor(away)||{}).luck_rating;
  const hv = (teamContextFor(home)||{}).luck_rating;
  if (av == null || hv == null || !isFinite(Number(av)) || !isFinite(Number(hv))) return `<span class="cfb-edge-pill even">—</span>`;
  // Betting-focused: less lucky / more negative gets the edge; high positive luck is fade risk.
  const diff = Number(hv) - Number(av);
  const count = cfbCheckCountByValueGap(diff, .75, 1.5, 2.5);
  if (!count) return `<span class="cfb-edge-pill even">—</span>`;
  return diff > 0 ? cfbEdgeBadge(away, count, 'away') : cfbEdgeBadge(home, count, 'home');
}
function cfbSosStepText(ctx){
  const step = ctx && ctx.overallStep ? `${escapeHtml(ctx.overallStep.label)} vs #${ctx.currentOverall || '—'}` : 'Step —';
  const overall = ctx && ctx.avgOverall != null ? `avg #${Math.round(ctx.avgOverall)} / max #${ctx.bestOverall || '—'}` : 'avg #— / max #—';
  const off = ctx && ctx.avgOppOff != null ? `avg #${Math.round(ctx.avgOppOff)} / max #${ctx.bestOppOff || '—'}` : 'avg #— / max #—';
  const def = ctx && ctx.avgOppDef != null ? `avg #${Math.round(ctx.avgOppDef)} / max #${ctx.bestOppDef || '—'}` : 'avg #— / max #—';
  return `${escapeHtml(step)}<div class="cfb-sos-summary"><span><b>Overall</b> ${escapeHtml(overall)}</span><span><b>Off test</b> ${escapeHtml(off)}</span><span><b>Def test</b> ${escapeHtml(def)}</span></div>`;
}
function cfbSpotChecklist(flags){
  const labels = ['B2B road','Off bye','Short rest','Lookahead','Sandwich'];
  const raw = (flags || []).map(f => String(f.label || f || '').toLowerCase().replace(/\s+/g,' ').trim());
  const aliases = {
    'B2B road':['b2b road','back-to-back road','back to back road','second straight road'],
    'Off bye':['off bye','bye week','post-bye','post bye'],
    'Short rest':['short rest','short week'],
    'Lookahead':['lookahead','look ahead'],
    'Sandwich':['sandwich']
  };
  return `<div class="cfb-spot-list">${labels.map(label => {
    const checked = (aliases[label] || [label.toLowerCase()]).some(a => raw.some(r => r.includes(a)));
    const cls = label === 'Off bye' ? 'good' : 'warn';
    return `<span class="cfb-spot-item ${cls}"><span class="cfb-spot-box ${checked ? 'checked' : ''}">${checked ? '✓' : ''}</span>${escapeHtml(label)}</span>`;
  }).join('')}</div>`;
}
function cfbBettingContextHtml(g){
  const away=g.away_team, home=g.home_team;
  const aFG=betCoachRank(away,'coach_betting'), hFG=betCoachRank(home,'coach_betting');
  const a1=betCoachRank(away,'coach_1h_betting'), h1=betCoachRank(home,'coach_1h_betting');
  const a2=betCoachRank(away,'coach_2h_betting'), h2=betCoachRank(home,'coach_2h_betting');
  const ac=teamContextFor(away)||{}, hc=teamContextFor(home)||{};
  const awayFlags=betSituationalFlags(g,away), homeFlags=betSituationalFlags(g,home);
  const awaySos=sosContextForTeam(away,g), homeSos=sosContextForTeam(home,g);
  const aAts=cfbCurrentAtsSummary(away,g,'fg'), hAts=cfbCurrentAtsSummary(home,g,'fg');
  const a1h=cfbCurrentAtsSummary(away,g,'1h'), h1h=cfbCurrentAtsSummary(home,g,'1h');
  const a2h=cfbCurrentAtsSummary(away,g,'2h'), h2h=cfbCurrentAtsSummary(home,g,'2h');
  return `<div class="cfb-section">
    <div class="cfb-section-title"><span>Betting Context</span><em class="cfb-edge-note">edge checkmarks: 1 small · 3 large · - = no edge</em></div>
    <table class="cfb-context-table"><thead><tr><th>Category</th><th>${escapeHtml(away)}</th><th>${escapeHtml(home)}</th><th>Edge <span class="cfb-edge-note">(- = no edge)</span></th></tr></thead><tbody>
      ${cfbContextRow('Coach ATS', cfbCoachValue(away,'coach_betting'), cfbCoachValue(home,'coach_betting'), cfbRankEdgeBadge(away,home,aFG,hFG))}
      ${cfbContextRow('Coach 1H ATS', cfbCoachValue(away,'coach_1h_betting'), cfbCoachValue(home,'coach_1h_betting'), cfbRankEdgeBadge(away,home,a1,h1))}
      ${cfbContextRow('Coach 2H ATS', cfbCoachValue(away,'coach_2h_betting'), cfbCoachValue(home,'coach_2h_betting'), cfbRankEdgeBadge(away,home,a2,h2))}
      ${cfbContextRow('2026 ATS', cfbCurrentAtsText(aAts), cfbCurrentAtsText(hAts), cfbCurrentAtsEdge(away,home,aAts,hAts))}
      ${cfbContextRow('2026 1H ATS', cfbCurrentAtsText(a1h), cfbCurrentAtsText(h1h), cfbCurrentAtsEdge(away,home,a1h,h1h))}
      ${cfbContextRow('2026 2H ATS', cfbCurrentAtsText(a2h), cfbCurrentAtsText(h2h), cfbCurrentAtsEdge(away,home,a2h,h2h))}
      ${cfbContextRow('Luck Rating', cfbLuckText(away), cfbLuckText(home), cfbLuckEdge(away,home))}
      ${cfbContextRow('Consistency', `#${ac.consistency_rank||'—'}`, `#${hc.consistency_rank||'—'}`, cfbRankEdgeBadge(away,home,ac.consistency_rank,hc.consistency_rank))}
      ${cfbContextRow('SOS / Step', cfbSosStepText(awaySos), cfbSosStepText(homeSos), cfbRankEdgeBadge(away,home,awaySos.avgOverall,homeSos.avgOverall))}
      ${cfbContextRow('Schedule Spot', cfbSpotChecklist(awayFlags), cfbSpotChecklist(homeFlags), cfbScheduleSpotEdge(away,home,awayFlags,homeFlags))}
    </tbody></table>
  </div>`;
}
function cfbScheduleSpotEdge(away, home, awayFlags, homeFlags){
  const bad = f => !String(f.cls || '').includes('good');
  const aBad = (awayFlags || []).filter(bad).length;
  const hBad = (homeFlags || []).filter(bad).length;
  const aGood = (awayFlags || []).filter(f => String(f.cls || '').includes('good')).length;
  const hGood = (homeFlags || []).filter(f => String(f.cls || '').includes('good')).length;
  const diff = (hBad - aBad) + (aGood - hGood); // positive means away cleaner/better
  const count = Math.abs(diff) >= 2 ? 2 : Math.abs(diff) === 1 ? 1 : 0;
  if (!count) return `<span class="cfb-edge-pill even">—</span>`;
  return diff > 0 ? cfbEdgeBadge(away, count, 'away') : cfbEdgeBadge(home, count, 'home');
}
function cfbOverallLeanHtml(g){
  const away=g.away_team, home=g.home_team;
  const as=betPreLineScore(g,away), hs=betPreLineScore(g,home);
  const leader=as>=hs?away:home;
  const diff=Math.abs(as-hs);
  const lean=diff>=20?'strong setup edge':diff>=10?'moderate setup edge':'thin / no clear setup edge';
  return `<div class="cfb-overall-lean"><div><b>Overall setup lean: ${escapeHtml(leader)}</b><br><span>Uses the existing Pre-Line Setup Score formula; layout-only patch.</span></div><div class="cfb-edge-pill ${leader===away?'away':'home'}">${as} - ${hs} · ${escapeHtml(lean)}</div></div>`;
}


/* MATCHUP_COACH_GRADE_CARD_START */
function fullGameCoachRowForTeam(team) {
  const rows = (DB && DB.coach_betting) || [];
  const target = typeof normName === 'function' ? normName(team) : String(team || '').toLowerCase().trim();
  return rows.find(r => {
    const n = typeof normName === 'function'
      ? normName(r.team || r.current_team)
      : String(r.team || r.current_team || '').toLowerCase().trim();
    return n === target;
  }) || null;
}

function fullGameCoachGrade(row) {
  if (!row) return {grade:'—', cls:'muted', label:'No full-game coach data'};
  const games = Number(row.games || row.ats_games || 0);
  if (!Number.isFinite(games) || games < 8) return {grade:'—', cls:'muted', label:`Tiny sample · ${games || 0} games`};

  const pct = Number(row.ats_win ?? row.ats_pct ?? row.ats_win_pct);
  const margin = Number(row.avg_ats ?? row.ats_margin ?? row.avg_cover_margin);
  let score = 0;
  if (Number.isFinite(pct)) score += (pct - 0.5) * 20;
  if (Number.isFinite(margin)) score += margin;
  score += Math.min(3, games / 10);

  const gradeObj = coachDisplayGrade(score, games, 'ats');
  const rec = row.ats_record || `${row.ats_w ?? '—'}-${row.ats_l ?? '—'}-${row.ats_push ?? 0}`;
  const pctTxt = Number.isFinite(pct) ? `${(pct * 100).toFixed(1)}%` : '—';
  const marginTxt = Number.isFinite(margin) ? `${margin >= 0 ? '+' : ''}${margin.toFixed(1)}` : '—';
  gradeObj.label = `${rec} ATS · ${pctTxt} · ATS +/- ${marginTxt} · ${gradeObj.label}`;
  return gradeObj;
}

function matchupCoachAtsGrade(team, half) {
  if (half === 'fg') return fullGameCoachGrade(fullGameCoachRowForTeam(team));

  const row = coachHalfRowForTeam(team, half);
  if (!row) return {grade:'—', cls:'muted', label:'No coach half ATS data'};
  const games = coachHalfNum(row, ['ats_games','games']) || 0;
  const score = coachHalfScore(row);
  const gradeObj = coachDisplayGrade(score, games, 'ats');
  const margin = coachHalfMargin(row);
  gradeObj.label = `${coachHalfRecord(row)} ATS · ${coachHalfPct(row)} · ATS +/- ${margin == null ? '—' : (margin >= 0 ? '+' : '') + margin.toFixed(1)} · ${gradeObj.label}`;
  return gradeObj;
}

function matchupCoachOuBestGrade(team, half) {
  const row = coachHalfRowForTeam(team, half);
  if (!row) return {side:'—', gradeObj:{grade:'—', cls:'muted', label:'No coach half O/U data'}};

  const overGrade = coachOuGrade(row, 'Over');
  const underGrade = coachOuGrade(row, 'Under');

  if ((underGrade.score ?? -999) > (overGrade.score ?? -999)) {
    return {side:'Under', gradeObj:underGrade};
  }
  return {side:'Over', gradeObj:overGrade};
}

function matchupCoachGradeCell(label, gradeObj) {
  return `<span class="matchup-coach-grade-cell" title="${escapeHtml(gradeObj && gradeObj.label || '')}">
    <span class="matchup-coach-grade-label">${escapeHtml(label)}</span>
    ${coachGradeBadge(gradeObj)}
  </span>`;
}

function matchupCoachOuCell(team, half) {
  const x = matchupCoachOuBestGrade(team, half);
  return matchupCoachGradeCell(x.side, x.gradeObj);
}

function matchupCoachGradesCard(g) {
  const away = g.away_team;
  const home = g.home_team;

  function row(team) {
    return `<tr>
      <td>${linkTeam(team)}</td>
      <td>${matchupCoachGradeCell('FG', matchupCoachAtsGrade(team, 'fg'))}</td>
      <td>${matchupCoachGradeCell('1H', matchupCoachAtsGrade(team, '1h'))}</td>
      <td>${matchupCoachGradeCell('2H', matchupCoachAtsGrade(team, '2h'))}</td>
      <td>${matchupCoachOuCell(team, '1h')}</td>
      <td>${matchupCoachOuCell(team, '2h')}</td>
    </tr>`;
  }

  return `<div class="card matchup-coach-grade-card">
    <div class="section-title">Coach Matchup Grades</div>
    <div class="small matchup-coach-grade-note">Grades combine ATS/O-U rate, margin vs line/total, and sample size. Hover grades for raw record details.</div>
    <div class="schedule-scroll">
      <table class="matchup-coach-grade-table">
        <thead>
          <tr>
            <th>Team</th>
            <th>Game ATS</th>
            <th>1H ATS</th>
            <th>2H ATS</th>
            <th>1H O/U Lean</th>
            <th>2H O/U Lean</th>
          </tr>
        </thead>
        <tbody>
          ${row(away)}
          ${row(home)}
        </tbody>
      </table>
    </div>
  </div>`;
}
/* MATCHUP_COACH_GRADE_CARD_END */


function matchupDetailHtml(g){
  const away = matchupForGameTeam(g, g.away_team);
  const home = matchupForGameTeam(g, g.home_team);
  const noEdgeNote = (!away && !home)
    ? `<div class="card" style="margin-bottom:10px;border-color:rgba(251,191,36,.28);background:rgba(251,191,36,.06)">
         <div class="section-title" style="font-size:14px;margin-bottom:4px">Production edge rows not loaded</div>
         <div class="small">No game_matchup_edges row matched this game yet. Showing available team-based matchup context, betting context, SOS, coach trends, and position ratings.</div>
       </div>`
    : '';
  return `<div class="matchup-panel">
    <div class="cfb-matchup-shell">
      ${cfbGameHeaderHtml(g)}
      ${noEdgeNote}
      ${spreadSetupDetailCard(g)}
      ${cfbPowerRatingsHtml(g)}
      ${cfbFourFactorsHtml(g)}
      ${cfbBettingContextHtml(g)}
      ${cfbOverallLeanHtml(g)}
      <details class="matchup-more-detail">
        <summary>More detail: position groups, tendency reads, SOS detail</summary>
        ${positionRatingsComparisonHtml(g)}
        <div class="matchup-compare-two-col">
          ${matchupComparisonStripForSide(g.away_team, g.home_team)}
          ${matchupComparisonStripForSide(g.home_team, g.away_team)}
        </div>
        ${matchupSOSContextHtml(g)}
        ${matchupCoachEdgeHtml(g)}
        <div class="matchup-two-col">${matchupPanelForSide(away)}${matchupPanelForSide(home)}</div>
      </details>
    </div>
  </div>`;
}
function matchupButton(g){
  const gid = matchupGameId(g);
  const safeId = String(gid).replace(/'/g, "\'");
  return `<button class="matchup-toggle" type="button" onclick="toggleMatchupRow('${safeId}'); event.stopPropagation();">Matchup</button><div class="small">${matchupCompactLabel(g)}</div>`;
}
function toggleMatchupRow(id){
  const row = document.getElementById(matchupDomIdFromGameId(id));
  if (!row) {
    console.warn('No matchup detail row found for', id, matchupDomIdFromGameId(id));
    return;
  }

  const opening = row.style.display === 'none' || row.style.display === '';

  if (opening && row.dataset.loaded !== '1') {
    const gid = String(id);
    const g = (DB.games || []).find(x => String(matchupGameId(x)) === gid);
    const cell = row.querySelector('td');
    if (cell && g) {
      cell.innerHTML = matchupDetailHtml(g);

      // Apply matchup UI polish immediately after lazy-loading season schedule matchup rows.
      setTimeout(() => {
        try {
          document.dispatchEvent(new Event('click'));
        } catch (e) {}
      }, 25);
      setTimeout(() => {
        try {
          document.dispatchEvent(new Event('click'));
        } catch (e) {}
      }, 150);
      setTimeout(() => {
        try {
          document.dispatchEvent(new Event('click'));
        } catch (e) {}
      }, 400);

      row.dataset.loaded = '1';
    }
  }

  row.style.display = opening ? 'table-row' : 'none';
}
function matchupScheduleDetailRow(g, colspan){
  return `<tr class="matchup-detail-row" id="${matchupDomId(g)}" data-loaded="0" style="display:none"><td colspan="${colspan}"><div class="muted">Loading matchup...</div></td></tr>`;
}
function matchupTeamScheduleBlock(g, team){ return `<details class="matchup-team-details"><summary>Matchup edges · ${escapeHtml(team)} vs ${escapeHtml(team === g.home_team ? g.away_team : g.home_team)}</summary>${matchupDetailHtml(g)}</details>`; }


function projectedSpreadInlineForTeam(g, teamName) {
  const pm = Number(g.projected_margin_home);
  if (!Number.isFinite(pm)) return '';

  // projected_margin_home is home-team perspective.
  // Positive = home favored. Negative = away favored.
  const favored = pm >= 0 ? g.home_team : g.away_team;
  if (String(teamName || '') !== String(favored || '')) return '';

  const pts = Math.abs(pm);
  const ptsText = Number.isInteger(pts) ? String(pts) : pts.toFixed(1).replace(/\.0$/, '');

  // Inline value only. No "Proj:" label.
  return ` <span class="marketlab-inline-proj-spread">-${ptsText}</span>`;
}

function marketLabTeamCellWithProj(g, teamName) {
  return `<span class="marketlab-team-inline-proj">${linkTeamWithComboRank(teamName)}${projectedSpreadInlineForTeam(g, teamName)}</span>`;
}


function gameInjuryCell(g) {
  const score = Number(g.game_injury_score || 0);
  const tier = String(g.game_injury_tier || 'None');
  const cls = tier.toLowerCase();
  const edge = Number(g.injury_edge_home || 0);
  const summary = g.injury_summary || '';

  if (!score || tier === 'None') {
    return '<span class="injury-chip injury-chip-none" title="No current injury impact flagged">INJ —</span>';
  }

  const edgeTxt = Number.isFinite(edge) && edge !== 0 ? ` · home edge ${edge > 0 ? '+' : ''}${edge.toFixed(1)}` : '';
  const label = `INJ ${score.toFixed(1)}`;
  const title = `${tier} injury impact${edgeTxt}`;

  return `<div class="injury-cell"><details><summary><span class="injury-chip injury-chip-${cls}" title="${escapeHtml(title)}">${escapeHtml(label)}</span></summary><div class="injury-detail-pop muted">${escapeHtml(summary || title)}</div></details></div>`;
}


function scheduleTable(games, mode='simple') {
  const view = mode || scheduleViewMode || 'simple';
  const sortedGames = sortScheduleGames(games);
  const header = view === 'odds'
    ? [
        scheduleTh('week','Week'), scheduleTh('date','Date'), scheduleTh('away','Away'), scheduleTh('home','Home'),
        scheduleSpreadTh('proj_spread','Proj Spread'), scheduleTh('market_spread','Market Spread'), scheduleTh('spread_edge','Spread Edge'),
        scheduleTh('proj_total','Proj Total'), scheduleTh('market_total','Market Total'), scheduleTh('total_edge','Total Edge'),
        scheduleTh('one_h_spread','SGO 1H Spread'), scheduleTh('one_h_total','SGO 1H Total'), scheduleTh('injury_score','Injuries'), '<th>Matchup</th>'
      ].join('')
    : view === 'marketlab'
      ? (scheduleMarketLabMode === 'totals'
        ? [
            scheduleTh('week','Week'), scheduleTh('date','Date'), scheduleTh('away','Away'), scheduleTh('home','Home'),
            scheduleTh('proj_total','Proj Total'), scheduleTh('market_total','Market Total'), scheduleTh('total_edge','Total Edge'),
            scheduleTh('total_ev','Total EV%'), scheduleTh('total_betscore','Total BetScore'), scheduleTh('injury_score','Injuries'), '<th>Matchup</th>'
          ].join('')
        : [
            scheduleTh('week','Week'), scheduleTh('date','Date'), scheduleTh('away','Away'), scheduleTh('home','Home'),
            scheduleTh('market_spread','Market Spread'), scheduleTh('spread_edge','ATS Edge'),
            scheduleTh('ats_ev','ATS EV%'), scheduleTh('ats_betscore','BetScore'), scheduleTh('injury_score','Injuries'), '<th>Matchup</th>'
          ].join(''))
      : view === 'results'
      ? [
          scheduleTh('week','Week'), scheduleTh('date','Date'), scheduleTh('away','Away'), scheduleTh('home','Home'),
          scheduleTh('status','Status'), scheduleTh('score','Score'), scheduleTh('winner','Winner'), scheduleTh('margin','Margin'),
          scheduleTh('total_pts','Total Pts'), scheduleTh('cfbd_id','CFBD ID'), scheduleTh('injury_score','Injuries'), '<th>Matchup</th>'
        ].join('')
      : [
          scheduleTh('week','Week'), scheduleTh('date','Date'), scheduleTh('away','Away'), scheduleTh('home','Home'),
          scheduleTh('conf','Conf'), scheduleTh('neutral','Neutral'), scheduleSpreadTh('proj_spread','Spread'),
          scheduleTh('proj_total','Total'), scheduleTh('home_win','Home Win %'), scheduleTh('status','Status'), scheduleTh('injury_score','Injuries'), '<th>Matchup</th>'
        ].join('');
  const colSpan = view === 'marketlab' ? (scheduleMarketLabMode === 'totals' ? 11 : 10) : view === 'odds' ? 14 : view === 'results' ? 12 : 12;
  const tableClass = view === 'marketlab' ? `schedule-table schedule-view-marketlab schedule-marketlab-${scheduleMarketLabMode}` : `schedule-table schedule-view-${view}`;
  return `<div class="card schedule-card"><div class="schedule-scroll"><table class="${tableClass}"><thead><tr>${header}</tr></thead><tbody>
  ${sortedGames.map(g => {
    const st = gameState(g);
    const res = gameResultParts(g);
    const ms = marketSpread(g), mt = marketTotal(g);
    const h1s = market1HSpread(g), h1t = market1HTotal(g);
    const spreadEdge = ms == null || ms === '' ? null : Number(g.projected_margin_home) + Number(ms);
    const totalEdge = mt == null || mt === '' ? null : Number(g.projected_total) - Number(mt);
    if (view === 'odds') return `<tr>
      <td>${g.week}</td><td class="marketlab-date-cell">${fmtDate(g.date)}</td><td>${linkTeamWithComboRank(g.away_team)}</td><td>${linkTeamWithComboRank(g.home_team)}</td>
      <td>${scheduleSpreadCell(g)}</td>
      <td>${fmtMarketSpreadCell(g)}</td><td>${fmtEdge(spreadEdge)}</td>
      <td>${fmtProjectedTotalSafe(g.projected_total)}</td><td>${fmtMarketTotalCell(g)}</td><td>${fmtEdge(totalEdge)}</td>
      <td>${fmtMarket1HSpreadCell(g)}</td><td>${fmtMarket1HTotalCell(g)}</td><td>${gameInjuryCell(g)}</td><td>${matchupButton(g)}</td>
    </tr>${matchupScheduleDetailRow(g, colSpan)}`;
      if (view === 'marketlab') {
        const ats = marketLabAtsMetrics(g);
        const tot = marketLabTotalMetrics(g);
        if (scheduleMarketLabMode === 'totals') {
          return `<tr>
            <td>${g.week}</td><td class="marketlab-date-cell">${fmtDate(g.date)}</td><td>${linkTeamWithComboRank(g.away_team)}</td><td>${linkTeamWithComboRank(g.home_team)}</td>
            <td>${fmtProjectedTotalSafe(g.projected_total)}</td><td>${fmtMarketTotalTwoSideCell(g)}</td><td>${fmtTotalSideWithCoachHalf(g, tot.side)}</td><td>${tot.ev}</td><td>${tot.score}</td>
            <td>${gameInjuryCell(g)}</td><td>${matchupButton(g)}</td>
          </tr>${matchupScheduleDetailRow(g, colSpan)}`;
        }
        return `<tr>
          <td>${g.week}</td><td class="marketlab-date-cell">${fmtDate(g.date)}</td><td>${marketLabTeamCellWithProj(g, g.away_team)}</td><td>${marketLabTeamCellWithProj(g, g.home_team)}</td>
          <td>${fmtMarketSpreadCompactCell(g)}</td><td>${fmtAtsSideWithCoachHalf(g, ats.side)}</td><td>${ats.ev}</td><td>${ats.score}</td>
          <td>${gameInjuryCell(g)}</td><td>${matchupButton(g)}</td>
        </tr>${matchupScheduleDetailRow(g, colSpan)}`;
      }
      if (view === 'results') return `<tr>
      <td>${g.week}</td><td class="marketlab-date-cell">${fmtDate(g.date)}</td><td>${linkTeamWithComboRank(g.away_team)}</td><td>${linkTeamWithComboRank(g.home_team)}</td>
      <td>${gameStatusChip(g)}</td><td>${gameScoreText(g)}</td><td>${res.winner==='—' ? '—' : linkTeam(res.winner)}</td><td>${res.margin === '—' ? '—' : fmtSigned(Number(res.margin))}</td><td>${res.total}</td><td>${st.cfbd_game_id || g.cfbd_game_id || '—'}</td><td>${gameInjuryCell(g)}</td><td>${matchupButton(g)}</td>
    </tr>${matchupScheduleDetailRow(g, colSpan)}`;
    return `<tr>
      <td>${g.week}</td>
      <td>${fmtDate(g.date)}</td>
      <td>${linkTeamWithComboRank(g.away_team)}</td>
      <td>${linkTeamWithComboRank(g.home_team)}</td>
      <td>${g.is_conference_game ? linkConf(g.home_conference) : '—'}</td>
      <td>${g.neutral_site ? 'Yes' : 'No'}</td>
      <td>${scheduleSpreadCell(g)}</td>
      <td>${fmtProjectedTotalSafe(g.projected_total)}</td>
      <td>${fmtPct(g.win_prob_home)}</td>
      <td>${gameStatusChip(g)}</td><td>${gameInjuryCell(g)}</td><td>${matchupButton(g)}</td>
    </tr>${matchupScheduleDetailRow(g, colSpan)}`;
  }).join('')}</tbody></table></div></div>`;
}


function bookLogoBadge(book) {
  const b = String(book || '').toLowerCase();
  let cls = 'book-logo-generic', label = book || 'Book';

  if (b.includes('draftkings') || b === 'dk') {
    cls = 'book-logo-dk'; label = 'DK';
  } else if (b.includes('fanduel') || b === 'fd') {
    cls = 'book-logo-fd'; label = 'FD';
  } else if (b.includes('betmgm') || b.includes('mgm')) {
    cls = 'book-logo-mgm'; label = 'MGM';
  } else if (b.includes('caesars') || b.includes('caesar')) {
    cls = 'book-logo-caesars'; label = 'CZ';
  }

  return `<span class="book-logo-badge ${cls}" title="${book || label}">${label}</span>`;
}
function bookHeaderLogo(book, sub='') {
  return `<div class="book-header-logo">${bookLogoBadge(book)}${sub ? `<div class="book-header-sub">${sub}</div>` : ''}</div>`;
}

function fmtMoney(v) {
  if (v == null || Number.isNaN(v)) return '—';
  const sign = v < 0 ? '-' : '';
  return sign + '$' + Math.abs(v).toFixed(1);
}
function fmtSigned(v) {
  if (v == null || Number.isNaN(v)) return '—';
  return (v>0?'+':'') + v.toFixed(1);
}
function betStatus(row) {
  const r = String(row['Result'] || '').trim().toLowerCase();
  if (r === 'win' || r === 'loss' || r === 'push') return r;
  return 'open';
}
function parseNum(v) {
  return v == null || v === '' ? null : Number(v);
}
function currentBetRows() {
  return bettingSeason === '2025' ? BETTING_2025_ROWS : BETTING_ROWS;
}
function getBettingFilteredRows() {
  const desc = byId('bDesc') ? byId('bDesc').value : 'all';
  const book = byId('bBook') ? byId('bBook').value : 'all';
  const status = byId('bStatus') ? byId('bStatus').value : 'all';
  const q = byId('bSearch') ? byId('bSearch').value.trim().toLowerCase() : '';
  return currentBetRows().filter(r => {
    if (desc !== 'all' && r['Bet Description'] !== desc) return false;
    if (book !== 'all' && r['Sportsbook'] !== book) return false;
    if (status !== 'all' && betStatus(r) !== status) return false;
    if (q) {
      const hay = [r['Bet'], r['Sport'], r['Source'], r['Account']].map(x => String(x || '').toLowerCase()).join(' | ');
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}
function summarizeBets(rows) {
  const settled = rows.filter(r => betStatus(r) !== 'open');
  const open = rows.filter(r => betStatus(r) === 'open');
  const wins = settled.filter(r => betStatus(r) === 'win').length;
  const losses = settled.filter(r => betStatus(r) === 'loss').length;
  const pushes = settled.filter(r => betStatus(r) === 'push').length;
  const risked = rows.reduce((s,r)=>s + (parseNum(r['Bet Amount']) || 0), 0);
  const openRisk = open.reduce((s,r)=>s + (parseNum(r['Bet Amount']) || 0), 0);
  const profit = settled.reduce((s,r)=>s + (parseNum(r['Profit']) || 0), 0);
  const roi = settled.length && risked ? profit / risked : null;
  const winRate = settled.length ? wins / (wins + losses || 1) : null;
  const clvVals = settled.map(r => parseNum(r['CLV'])).filter(v => v != null && !Number.isNaN(v));
  const avgClv = clvVals.length ? clvVals.reduce((a,b)=>a+b,0) / clvVals.length : null;
  return {
    bets: rows.length, settled: settled.length, open: open.length, wins, losses, pushes,
    risked, openRisk, profit, roi, winRate, avgClv
  };
}
function bettingTable(rows) {
  if (!rows.length) return '<div class="card"><div class="muted">No bets match the current filters.</div></div>';
  return `<div class="card" style="overflow:auto"><table><thead><tr>
    <th>Date</th><th>Account</th><th>Description</th><th>Book</th><th>Sport</th><th>Bet</th><th>Market</th><th>Line</th><th>Price</th><th>Status</th><th>Profit</th><th>CLV</th><th>EV</th>
  </tr></thead><tbody>
    ${rows.map(r => {
      const st = betStatus(r);
      const profit = parseNum(r['Profit']);
      const clv = parseNum(r['CLV']);
      const ev = parseNum(r['EV']);
      return `<tr>
        <td>${fmtDate(r['Date'])}</td>
        <td>${r['Account'] || '—'}</td>
        <td>${r['Bet Description'] || '—'}</td>
        <td>${r['Sportsbook'] || '—'}</td>
        <td>${r['Sport'] || '—'}</td>
        <td>${r['Bet'] || '—'}</td>
        <td>${r['Bet Type'] || '—'}</td>
        <td>${r['Bet Line'] ?? '—'}</td>
        <td>${r['Bet Price'] ?? '—'}</td>
        <td>${st === 'open' ? '<span class="tag">Open</span>' : `<span class="tag ${st==='win'?'pos':st==='loss'?'neg':''}">${st[0].toUpperCase()+st.slice(1)}</span>`}</td>
        <td class="${profit>0?'pos':profit<0?'neg':''}">${st==='open' ? '—' : fmtMoney(profit)}</td>
        <td>${clv == null ? '—' : fmtSigned(clv)}</td>
        <td>${ev == null ? '—' : fmtSigned(ev)}</td>
      </tr>`;
    }).join('')}
  </tbody></table></div>`;
}
function bettingBreakdown(rows, field, valueFormatter=null) {
  const map = new Map();
  rows.forEach(r => {
    const k = r[field] || '—';
    if (!map.has(k)) map.set(k, []);
    map.get(k).push(r);
  });
  const items = [...map.entries()].map(([key, vals]) => {
    const s = summarizeBets(vals);
    return { key, ...s };
  }).sort((a,b)=>b.bets-a.bets);
  return `<table><thead><tr><th>${field}</th><th>Bets</th><th>Open</th><th>Settled</th><th>Profit</th></tr></thead><tbody>
    ${items.map(it=>`<tr><td>${valueFormatter ? valueFormatter(it.key) : it.key}</td><td>${it.bets}</td><td>${it.open}</td><td>${it.settled}</td><td class="${it.profit>0?'pos':it.profit<0?'neg':''}">${it.settled?fmtMoney(it.profit):'—'}</td></tr>`).join('')}
  </tbody></table>`;
}

const coachSortLabels = {
  ats_rank: 'ATS Rank',
  team: 'Team',
  head_coach: 'Coach',
  seasons_tracked: 'Yrs',
  ats_pct: 'ATS %',
  avg_ats_margin: 'ATS +/-',
  over_pct: 'Over %',
  avg_total_margin: 'Total +/-'
};
function coachSortValue(r, key) {
  if (key === 'team' || key === 'head_coach') return String(r[key] || '').toLowerCase();
  return r[key];
}
function sortedCoachBettingRows() {
  const {key, dir} = coachSortState;
  const mult = dir === 'asc' ? 1 : -1;
  const f = coachFilterText.trim().toLowerCase();
  return [...currentCoachTrendRows()]
    .filter(r => !f || String(r.team || '').toLowerCase().includes(f) || String(r.head_coach || '').toLowerCase().includes(f) || String(r.teams_tracked || '').toLowerCase().includes(f))
    .sort((a,b) => {
      let av = coachSortValue(a,key), bv = coachSortValue(b,key);
      const aMissing = av === undefined || av === null || Number.isNaN(av);
      const bMissing = bv === undefined || bv === null || Number.isNaN(bv);
      if (aMissing && bMissing) return String(a.team || '').localeCompare(String(b.team || ''));
      if (aMissing) return 1;
      if (bMissing) return -1;
      if (typeof av === 'string' || typeof bv === 'string') {
        const cmp = String(av).localeCompare(String(bv));
        return cmp !== 0 ? cmp * mult : (a.ats_rank || 999) - (b.ats_rank || 999);
      }
      if (av === bv) return (a.ats_rank || 999) - (b.ats_rank || 999);
      return (av - bv) * mult;
    });
}
function coachSortArrow(key) {
  return coachSortState.key === key ? `<span class="sort-arrow">${coachSortState.dir === 'asc' ? '▲' : '▼'}</span>` : '';
}
function coachSortableTh(key, label) {
  return `<th class="sortable" onclick="setCoachSort('${key}')">${label}${coachSortArrow(key)}</th>`;
}
function setCoachSort(key) {
  if (coachSortState.key === key) coachSortState.dir = coachSortState.dir === 'asc' ? 'desc' : 'asc';
  else {
    coachSortState.key = key;
    coachSortState.dir = (key === 'team' || key === 'head_coach' || key === 'ats_rank') ? 'asc' : 'desc';
  }
  if ((location.hash || '#/') !== '#coach-betting') location.hash = '#coach-betting';
  else route();
}
function mountCoachBettingControls() {
  const search = byId('coachBettingSearch');
  const select = byId('coachSortSelect');
  const dirBtn = byId('coachSortDirBtn');
  if (search) {
    search.value = coachFilterText;
    search.addEventListener('input', e => { coachFilterText = e.target.value; route(); });
  }
  if (select) {
    select.value = coachSortState.key;
    select.addEventListener('change', e => setCoachSort(e.target.value));
  }
  if (dirBtn) {
    dirBtn.textContent = coachSortState.dir === 'asc' ? 'Ascending' : 'Descending';
    dirBtn.addEventListener('click', () => { coachSortState.dir = coachSortState.dir === 'asc' ? 'desc' : 'asc'; route(); });
  }
}
function renderCoachBettingMobileCard(r) {
  return `<div class="rank-card">
    <div class="rank-card-head">
      <div>
        <div class="rank-card-title">${r.head_coach || '—'}</div>
        <div class="small">${linkTeam(r.team)}</div>
      </div>
      <div class="rank-card-rank">ATS #${r.ats_rank || '—'}</div>
    </div>
    <div class="rank-card-grid">
      <div class="rank-stat"><div class="label">ATS</div><div class="value">${r.ats_record || '—'}</div></div>
      <div class="rank-stat"><div class="label">ATS %</div><div class="value">${fmtPct(r.ats_pct)}</div></div>
      <div class="rank-stat"><div class="label">ATS +/-</div><div class="value ${fmtSignedClass(r.avg_ats_margin)}">${fmtSigned(r.avg_ats_margin)}</div></div>
      <div class="rank-stat"><div class="label">O/U</div><div class="value">${r.ou_record || '—'}</div></div>
      <div class="rank-stat"><div class="label">Over %</div><div class="value">${fmtPct(r.over_pct)}</div></div>
      <div class="rank-stat"><div class="label">Total +/-</div><div class="value ${fmtSignedClass(r.avg_total_margin)}">${fmtSigned(r.avg_total_margin)}</div></div>
    </div>
    <div class="small">Tracked seasons: ${r.first_season || '—'}-${r.last_season || '—'} · ${r.seasons_tracked || '—'} yrs</div>
  </div>`;
}
function renderCoachBetting() {
  const rows = sortedCoachBettingRows();
  const activeRows = currentCoachTrendRows();
  const avgAts = avg(activeRows.map(r => r.ats_pct).filter(v => v != null && isFinite(v)));
  const avgMargin = avg(activeRows.map(r => r.avg_ats_margin).filter(v => v != null && isFinite(v)));
  const bestAts = [...activeRows].filter(r => r.ats_pct != null).sort((a,b) => b.ats_pct - a.ats_pct)[0];
  const bestMargin = [...activeRows].filter(r => r.avg_ats_margin != null).sort((a,b) => b.avg_ats_margin - a.avg_ats_margin)[0];
  return `
    <div class="hero">
      <div>
        <div class="page-title">Coach Betting Trends · ${currentCoachTrendLabel()}</div>
        <div class="page-sub">Current 2026 team head coaches with ATS and over/under records. Use the period buttons to switch between full game, 1st half, and 2nd half. 1H/2H data is partial through 2025-09-14.</div>
      </div>
      <div class="hero-stats">
        <div class="mini"><div class="label">Coaches</div><div class="value">${activeRows.length}</div></div>
        <div class="mini"><div class="label">Avg ATS %</div><div class="value">${fmtPct(avgAts)}</div></div>
        <div class="mini"><div class="label">Avg ATS +/-</div><div class="value ${fmtSignedClass(avgMargin)}">${fmtSigned(avgMargin)}</div></div>
        <div class="mini"><div class="label">Top ATS %</div><div class="value">${bestAts ? bestAts.head_coach : '—'}</div></div>
      </div>
    </div>
    <div class="filters">
      <button class="pill" onclick="setCoachTrendPeriod('game')" style="${coachTrendPeriod==='game'?'background:#183468;border-color:#4470ba':''}">Full Game</button>
      <button class="pill" onclick="setCoachTrendPeriod('1h')" style="${coachTrendPeriod==='1h'?'background:#183468;border-color:#4470ba':''}">1st Half</button>
      <button class="pill" onclick="setCoachTrendPeriod('2h')" style="${coachTrendPeriod==='2h'?'background:#183468;border-color:#4470ba':''}">2nd Half</button>
      <input id="coachBettingSearch" placeholder="Search coach, team, tracked teams">
      <select id="coachSortSelect">${Object.entries(coachSortLabels).map(([key,label])=>`<option value="${key}">Sort by ${label}</option>`).join('')}</select>
      <button id="coachSortDirBtn" class="pill" type="button">${coachSortState.dir === 'asc' ? 'Ascending' : 'Descending'}</button>
      <div class="small" style="align-self:center">${rows.length} rows shown</div>
    </div>
    <div class="card desktop-rankings market-board-card" style="margin-top:16px">
      <table><thead><tr>
        ${coachSortableTh('ats_rank','ATS Rank')}
        ${coachSortableTh('team','Team')}
        ${coachSortableTh('head_coach','Coach')}
        ${coachSortableTh('seasons_tracked','Yrs')}
        <th>ATS</th>
        ${coachSortableTh('ats_pct','ATS %')}
        ${coachSortableTh('avg_ats_margin','ATS +/-')}
        <th>O/U</th>
        ${coachSortableTh('over_pct','Over %')}
        ${coachSortableTh('avg_total_margin','Total +/-')}
      </tr></thead><tbody>
      ${rows.map(r=>`<tr>
        <td>${r.ats_rank || '—'}</td>
        <td>${linkTeam(r.team)}</td>
        <td>${r.head_coach || '—'}</td>
        <td>${r.seasons_tracked || '—'}</td>
        <td>${r.ats_record || '—'}</td>
        <td>${fmtPct(r.ats_pct)}</td>
        <td class="${fmtSignedClass(r.avg_ats_margin)}">${fmtSigned(r.avg_ats_margin)}</td>
        <td>${r.ou_record || '—'}</td>
        <td>${fmtPct(r.over_pct)}</td>
        <td class="${fmtSignedClass(r.avg_total_margin)}">${fmtSigned(r.avg_total_margin)}</td>
      </tr>`).join('')}
      </tbody></table>
    </div>
    <div class="card mobile-rankings" style="margin-top:12px">
      ${rows.map(renderCoachBettingMobileCard).join('')}
    </div>
  `;
}

function renderBetting() {
  const rows = currentBetRows();
  const s = summarizeBets(rows);
  const descs = [...new Set(rows.map(r => r['Bet Description']).filter(Boolean))].sort();
  const books = [...new Set(rows.map(r => r['Sportsbook']).filter(Boolean))].sort();
  const liveSheet = bettingSeason === '2025' ? BETTING_SHEET_URL.replace('gid=938568824','gid=1629429397') : BETTING_SHEET_URL;
  const liveCsv = bettingSeason === '2025' ? BETTING_2025_CSV_URL : BETTING_CSV_URL;
  return `
    <div class="hero">
      <div>
        <div class="page-title">Betting</div>
        <div class="page-sub">Analytics page styled to match the site. Summary cards and tables are computed from the uploaded betting workbook snapshot, with your live Google Sheet linked below.</div>
      </div>
      <div class="hero-stats">
        <button class="pill" onclick="setBettingSeason('2026')" style="${bettingSeason==='2026'?'background:#183468;border-color:#4470ba':''}">2026</button>
        <button class="pill" onclick="setBettingSeason('2025')" style="${bettingSeason==='2025'?'background:#183468;border-color:#4470ba':''}">2025</button>
        <a class="pill" href="${liveSheet}" target="_blank" rel="noopener">Open Live Google Sheet</a>
        <a class="pill" href="${liveCsv}" target="_blank" rel="noopener">Open CSV</a>
      </div>
    </div>
    <div class="grid cols-4" style="margin-top:16px">
      <div class="card"><div class="kpi">Bets</div><div class="kpi-value">${s.bets}</div><div class="kpi-sub">${s.open} open · ${s.settled} settled</div></div>
      <div class="card"><div class="kpi">Exposure</div><div class="kpi-value">${fmtMoney(s.openRisk)}</div><div class="kpi-sub">Current risk on open bets</div></div>
      <div class="card"><div class="kpi">Record</div><div class="kpi-value">${s.settled ? `${s.wins}-${s.losses}${s.pushes?`-${s.pushes}`:''}` : '—'}</div><div class="kpi-sub">${s.winRate == null ? 'No graded bets yet' : fmtPct(s.winRate) + ' win rate'}</div></div>
      <div class="card"><div class="kpi">ROI</div><div class="kpi-value">${s.roi == null ? '—' : fmtPct(s.roi)}</div><div class="kpi-sub">${s.settled ? fmtMoney(s.profit) + ' profit' : 'Profit starts when bets are graded'}</div></div>
    </div>
    <div class="grid cols-4" style="margin-top:16px">
      <div class="card"><div class="kpi">Profit</div><div class="kpi-value ${s.profit>0?'pos':s.profit<0?'neg':''}">${s.settled ? fmtMoney(s.profit) : '—'}</div><div class="kpi-sub">Settled bets only</div></div>
      <div class="card"><div class="kpi">CLV</div><div class="kpi-value">${s.avgClv == null ? '—' : fmtSigned(s.avgClv)}</div><div class="kpi-sub">Average settled CLV</div></div>
      <div class="card"><div class="kpi">Avg Bet</div><div class="kpi-value">${fmtMoney(s.bets ? s.risked / s.bets : 0)}</div><div class="kpi-sub">Across current filtered bets</div></div>
      <div class="card"><div class="kpi">Season</div><div class="kpi-value">${bettingSeason}</div><div class="kpi-sub">Switch between 2026 and 2025 betting data</div></div>
    </div>
    <div class="filters">
      <select id="bDesc"><option value="all">All descriptions</option>${descs.map(v=>`<option value="${v}">${v}</option>`).join('')}</select>
      <select id="bBook"><option value="all">All sportsbooks</option>${books.map(v=>`<option value="${v}">${v}</option>`).join('')}</select>
      <select id="bStatus"><option value="all">All statuses</option><option value="open">Open</option><option value="win">Win</option><option value="loss">Loss</option><option value="push">Push</option></select>
      <input id="bSearch" placeholder="Search bet, source, account, sport">
    </div>
    <div id="bettingSummaryWrap"></div>
    <div class="grid cols-2" style="margin-top:16px">
      <div class="card">
        <div class="section-title">Live Sheet</div>
        <div class="small">Published Google Sheet embedded for the selected season.</div>
        <div style="margin-top:14px"><iframe class="sheet-frame" src="${BETTING_SHEET_URL + '&widget=true&headers=false'}" loading="lazy"></iframe></div>
      </div>
      <div class="card">
        <div class="section-title">How this page works</div>
        <div class="list-item"><div><b>Analytics</b><div class="muted">Computed from the uploaded workbook snapshot you shared in chat.</div></div></div>
        <div class="list-item"><div><b>Live sheet</b><div class="muted">Embedded from your published Google Sheet so you can keep browsing the newest version.</div></div></div>
        <div class="list-item"><div><b>Record / ROI / Profit</b><div class="muted">These use graded bets only. Blank Result values are treated as open bets.</div></div></div>
        <div class="list-item"><div><b>CLV</b><div class="muted">Shown when the CLV column is filled in on settled bets.</div></div></div>
      </div>
    </div>
  `;
}
function mountBettingFilters() {
  function draw() {
    const rows = getBettingFilteredRows();
    const s = summarizeBets(rows);
    byId('bettingSummaryWrap').innerHTML = `
      <div class="grid cols-3">
        <div>${bettingTable(rows)}</div>
        <div class="card">
          <div class="section-title">By Bet Description</div>
          ${bettingBreakdown(rows, 'Bet Description')}
        </div>
        <div class="card">
          <div class="section-title">By Sportsbook</div>
          ${bettingBreakdown(rows, 'Sportsbook')}
          <div class="section-title" style="margin-top:18px">Filtered Snapshot</div>
          <div class="small">Bets: ${s.bets}</div>
          <div class="small" style="margin-top:6px">Open: ${s.open}</div>
          <div class="small" style="margin-top:6px">Settled: ${s.settled}</div>
          <div class="small" style="margin-top:6px">Exposure: ${fmtMoney(s.openRisk)}</div>
          <div class="small" style="margin-top:6px">Profit: ${s.settled ? fmtMoney(s.profit) : '—'}</div>
          <div class="small" style="margin-top:6px">ROI: ${s.roi == null ? '—' : fmtPct(s.roi)}</div>
        </div>
      </div>`;
  }
  ['bDesc','bBook','bStatus','bSearch'].forEach(id => byId(id).addEventListener('input', draw));
  draw();
}

function dashboardCounts() {
  return (DB.dashboard && DB.dashboard.counts) || {};
}

function dashNum(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function dashText(v) {
  if (v == null || v === '') return '';
  return escapeHtml(String(v));
}

function dashboardCard(title, value, sub='') {
  return `<div class="card"><div class="kpi">${escapeHtml(title)}</div><div class="kpi-value">${value}</div>${sub ? `<div class="kpi-sub">${sub}</div>` : ''}</div>`;
}


function dashboardArbTitle(row) {
  if (!row) return '—';
  if (row.dashboard_title) return row.dashboard_title;
  const team = row.team || row.side || row.market || '';
  const typ = row.type || 'Arb';
  const edge = row.edge_pct != null && row.edge_pct !== '' ? ` ${Number(row.edge_pct).toFixed(2)}%` : '';
  if (row.title && String(row.title).toLowerCase() !== 'betting angle') return row.title;
  if (team) return `${typ}: ${team}${edge}`;
  if (row.summary) return row.summary;
  if (row.reason) return row.reason;
  return `${typ}${edge}`;
}

function dashboardBestMoveTitle(row) {
  if (!row) return '—';
  if (row.title) return row.title;
  if (row.summary) return row.summary;
  const game = [row.away_team, row.home_team].filter(Boolean).join(' at ');
  if (game) return `${game} ${row.market || 'line'} moved`;
  return 'Market move';
}

function dashboardStatusLine(dash, counts) {
  const parts = [
    `<b>${dashNum(counts.action_games)}</b> Action games`,
    `<b>${dashNum(counts.game_line_edges)}</b> game edges`,
    `<b>${dashNum(counts.arbitrage_angles)}</b> arbs/middles`,
    `<b>${dashNum(counts.market_moves)}</b> market moves`
  ];
  const latest = dash && dash.data_status && dash.data_status.latest_action_pull
    ? String(dash.data_status.latest_action_pull).slice(0, 19).replace('T', ' ')
    : '';
  if (latest) parts.push(`<b>Latest pull:</b> ${escapeHtml(latest)}`);
  return `<div class="dashboard-status">${parts.join(' · ')}</div>`;
}

function dashboardAngleCard(row, kind='edge') {
  if (!row) return '';
  const title = kind === 'arb' ? dashboardArbTitle(row) : (row.title || row.summary || row.reason || 'Betting angle');
  const reason = row.dashboard_summary || row.reason || row.summary || '';
  const team = row.team || '';
  const book = row.book || '';
  const line = row.current_line || row.projected_line || '';
  const week = row.game_week || row.week || '';
  const ev = row.ev_pct;
  const score = row.score;
  const edge = row.edge_pct;
  const move = row.change;

  let right = '';
  if (ev != null && ev !== '') right = `EV ${Number(ev).toFixed(1)}%`;
  else if (edge != null && edge !== '') right = `ARB ${Number(edge).toFixed(2)}%`;
  else if (score != null && score !== '') right = `Score ${Number(score).toFixed(0)}`;
  else if (move != null && move !== '') right = `Move ${move}`;

  const pills = [
    team ? `Team: ${team}` : '',
    book ? `Book: ${book}` : '',
    line ? `${line}` : '',
    week ? `Week ${week}` : ''
  ].filter(Boolean).map(x => `<span class="dashboard-pill">${dashText(x)}</span>`).join('');

  return `<div class="dashboard-angle">
    <div class="dashboard-angle-top">
      <div>
        <div class="dashboard-angle-title">${dashText(title)}</div>
        ${reason ? `<div class="dashboard-angle-meta">${dashText(reason)}</div>` : ''}
      </div>
      ${right ? `<div class="dashboard-angle-score">${dashText(right)}</div>` : ''}
    </div>
    ${pills ? `<div class="dashboard-pill-row">${pills}</div>` : ''}
  </div>`;
}

function dashboardList(rows, kind='edge', limit=5) {
  const arr = Array.isArray(rows) ? rows.slice(0, limit) : [];
  if (!arr.length) return `<div class="dashboard-empty">No current items for this run.</div>`;
  return `<div class="dashboard-angle-list">${arr.map(r => dashboardAngleCard(r, kind)).join('')}</div>`;
}

function dashboardGameMoveCard(row) {
  if (!row) return '';
  const game = `${row.away_team || ''} at ${row.home_team || ''}`.trim();
  const title = dashboardBestMoveTitle(row) || (game ? `${game} — ${row.market || 'Game line'}` : (row.summary || 'Game line move'));
  const book = row.book || '';
  const prev = row.previous;
  const latest = row.latest;
  const summary = row.summary || '';
  return `<div class="dashboard-angle">
    <div class="dashboard-angle-top">
      <div>
        <div class="dashboard-angle-title">${dashText(title)}</div>
        <div class="dashboard-angle-meta">${dashText(book)} moved ${dashText(prev)} → ${dashText(latest)}</div>
      </div>
      ${row.change != null && row.change !== '' ? `<div class="dashboard-angle-score">${dashText(row.change)}</div>` : ''}
    </div>
    ${summary ? `<div class="dashboard-pill-row"><span class="dashboard-pill">${dashText(summary)}</span></div>` : ''}
  </div>`;
}

function dashboardGameMoveList(rows, limit=5) {
  const arr = Array.isArray(rows) ? rows.slice(0, limit) : [];
  if (!arr.length) return `<div class="dashboard-empty">No current game line moves for this run.</div>`;
  return `<div class="dashboard-angle-list">${arr.map(r => dashboardGameMoveCard(r)).join('')}</div>`;
}

function renderHome() {
  const top = DB.teams.slice(0,25);
  const featured = [...DB.games]
    .filter(g=>g.week===1 && Number.isFinite(Number(g.projected_margin_home)) && Number.isFinite(Number(g.projected_total)) && Number.isFinite(Number(g.win_prob_home)))
    .sort((a,b)=>Math.abs(Number(a.projected_margin_home))-Math.abs(Number(b.projected_margin_home)))
    .slice(0,8);
  const titleFavorites = DB.conferences.map(c=>({conference:c.conference, favorite:c.teams[0]})).sort((a,b)=>b.favorite.conference_title_pct-a.favorite.conference_title_pct);
  const dash = DB.dashboard || {};
  const counts = dashboardCounts();
  const bestEdge = (dash.top_game_edges || [])[0];
  const bestArb = (dash.top_arbs || [])[0];
  const bestMove = (dash.top_market_moves || [])[0] || (dash.top_game_moves || [])[0];

  return `
    <div class="hero">
      <div>
        <div class="page-title">Daily Betting Dashboard</div>
        <div class="page-sub">Actionable market edges, line moves, arbs/middles, and data status from the latest automated update.</div>
      </div>
      <div class="hero-stats">
        <div class="mini"><div class="label">Game Edges</div><div class="value">${dashNum(counts.game_line_edges)}</div></div>
        <div class="mini"><div class="label">Arbs / Middles</div><div class="value">${dashNum(counts.arbitrage_angles)}</div></div>
        <div class="mini"><div class="label">Market Moves</div><div class="value">${dashNum(counts.market_moves)}</div></div>
        <div class="mini"><div class="label">Action Games</div><div class="value">${dashNum(counts.action_games)}</div></div>
      </div>
      <div class="dashboard-quick-actions">
        <a class="dashboard-action-btn" href="#schedule" onclick="setScheduleViewMode && setScheduleViewMode('marketlab')">Open Market Lab →</a>
        <a class="dashboard-action-btn" href="#futures">Open Arbs →</a>
        <a class="dashboard-action-btn" href="#futures">Open Daily Moves →</a>
        <a class="dashboard-action-btn" href="#schedule">Open Schedule →</a>
      </div>
      ${dashboardStatusLine(dash, counts)}
    </div>

    <div class="grid cols-4" style="margin-top:16px">
      ${dashboardCard('Best Game Edge', bestEdge ? dashText(bestEdge.title || 'Game edge') : '—', bestEdge && bestEdge.ev_pct != null ? `EV ${Number(bestEdge.ev_pct).toFixed(1)}% · ${dashText(bestEdge.book || '')}` : 'From Market Lab')}
      ${dashboardCard('Best Arb / Middle', bestArb ? dashText(dashboardArbTitle(bestArb)) : '—', bestArb && bestArb.edge_pct != null ? `ARB ${Number(bestArb.edge_pct).toFixed(2)}%` : 'From market scan')}
      ${dashboardCard('Biggest Move', bestMove ? dashText(dashboardBestMoveTitle(bestMove)) : '—', bestMove && bestMove.team ? dashText(bestMove.team) : 'Latest movement')}
      ${dashboardCard('Latest Line Pull', dash.data_status && dash.data_status.latest_action_pull ? dashText(String(dash.data_status.latest_action_pull).slice(0,10)) : '—', 'Action Network game lines')}
    </div>

    <div class="grid cols-2" style="margin-top:16px">
      <div class="card">
        <div class="section-title">Priority Game Line Edges</div>
        <div class="dashboard-section-sub">Top Market Lab spread/total edges using current best available lines.</div>
        ${dashboardList(dash.top_game_edges, 'edge', 6)}
        <div style="margin-top:12px"><a class="dashboard-card-link" href="#schedule" onclick="setScheduleViewMode && setScheduleViewMode('marketlab')">Open Market Lab →</a></div>
      </div>
      <div class="card">
        <div class="section-title">Arbs / Middles</div>
        <div class="dashboard-section-sub">Best current market inefficiencies from the arb/middle scan.</div>
        ${dashboardList(dash.top_arbs, 'arb', 6)}
        <div style="margin-top:12px"><a class="dashboard-card-link" href="#futures">Open Futures Market →</a></div>
      </div>
    </div>

    <div class="grid cols-2" style="margin-top:16px">
      <div class="card">
        <div class="section-title">Win Total / Futures Moves</div>
        <div class="dashboard-section-sub">Recent moves from the daily betting angles report.</div>
        ${dashboardList(dash.top_market_moves, 'move', 6)}
      </div>
      <div class="card">
        <div class="section-title">Game Line Moves</div>
        <div class="dashboard-section-sub">Best current edge-line moves after stale backups are hidden.</div>
        ${dashboardGameMoveList(dash.top_game_moves, 6)}
      </div>
    </div>

    <div class="hero" style="margin-top:16px">
      <div>
        <div class="page-title">2026 NCAA Football</div>
        <div class="page-sub">Season snapshot, rankings, simulations, and conference title probabilities.</div>
      </div>
      <div class="hero-stats">
        <div class="mini"><div class="label">Teams</div><div class="value">${DB.meta.counts.teams}</div></div>
        <div class="mini"><div class="label">Games</div><div class="value">${DB.meta.counts.games}</div></div>
        <div class="mini"><div class="label">Simulated Games</div><div class="value">${DB.meta.counts.simulated_games ?? DB.meta.counts.games}</div></div>
        <div class="mini"><div class="label">Conferences</div><div class="value">${DB.meta.counts.conferences}</div></div>
      </div>
    </div>

    <div class="grid cols-4" style="margin-top:16px">
      <div class="card"><div class="kpi">Top Team</div><div class="kpi-value">${teamLabel(top[0].team)}</div><div class="kpi-sub">Rank #${top[0].rank} · Power Rating ${top[0].combo.toFixed(1)}</div></div>
      <div class="card"><div class="kpi">Best Avg Wins</div><div class="kpi-value">${teamLabel([...DB.teams].sort((a,b)=>b.avg_total_wins-a.avg_total_wins)[0].team)}</div><div class="kpi-sub">${[...DB.teams].sort((a,b)=>b.avg_total_wins-a.avg_total_wins)[0].avg_total_wins.toFixed(2)} projected wins</div></div>
      <div class="card"><div class="kpi">Highest Bowl %</div><div class="kpi-value">${teamLabel([...DB.teams].sort((a,b)=>b.bowl_eligibility_pct-a.bowl_eligibility_pct)[0].team)}</div><div class="kpi-sub">${fmtPct([...DB.teams].sort((a,b)=>b.bowl_eligibility_pct-a.bowl_eligibility_pct)[0].bowl_eligibility_pct)}</div></div>
      <div class="card"><div class="kpi">Strongest League Favorite</div><div class="kpi-value">${teamLabel(titleFavorites[0].favorite.team)}</div><div class="kpi-sub">${titleFavorites[0].conference} · ${fmtPct(titleFavorites[0].favorite.conference_title_pct)}</div></div>
    </div>

    <div class="grid cols-2" style="margin-top:16px">
      <div class="card">
        <div class="section-title">Top 25</div>
        <table><thead><tr><th>Rank</th><th>Team</th><th>Conf</th><th>Power Rating</th><th>Avg Wins</th></tr></thead><tbody>
        ${top.map(t=>`<tr><td>${t.rank}</td><td>${linkTeam(t.team)}</td><td>${linkConf(t.conference)}</td><td>${t.combo.toFixed(1)}</td><td>${t.avg_total_wins.toFixed(2)}</td></tr>`).join('')}
        </tbody></table>
      </div>
      <div class="card">
        <div class="section-title">Week 1 Featured Games</div>
        ${featured.map(g=>`<div class="list-item">
          <div><div><b>${linkTeam(g.away_team)} at ${linkTeam(g.home_team)}</b></div><div class="small">${fmtDate(g.date)} · ${g.neutral_site ? 'Neutral site' : 'Campus site'}</div></div>
          <div style="text-align:right"><div>${spreadText(g)}</div><div class="small">Total ${fmtProjectedTotalSafe(g.projected_total)} · Home ${fmtPct(g.win_prob_home)}</div></div>
        </div>`).join('')}
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="section-title">Conference Title Favorites</div>
      <table><thead><tr><th>Conference</th><th>Favorite</th><th>Title %</th><th>Avg Strength</th><th>Teams</th></tr></thead><tbody>
      ${DB.conferences.map(c=>`<tr><td>${linkConf(c.conference)}</td><td>${linkTeam(c.teams[0].team)}</td><td>${fmtPct(c.teams[0].conference_title_pct)}</td><td>${c.average_strength.toFixed(1)}</td><td>${c.num_teams}</td></tr>`).join('')}
      </tbody></table>
    </div>
  `;
}
function renderSchedule() {
  const weeks = [...new Set(DB.games.map(g=>g.week))].sort((a,b)=>a-b);
  const cfbdTagged = DB.games.filter(g => g.cfbd_game_id || g.cfbd_status || g.cfbd_completed || g.completed).length;
  const finalTagged = DB.games.filter(g => gameState(g).status === 'final').length;
  return `
    <div class="page-title">Season Schedule</div>
    ${ratingsWeightLabPanel()}
    <div class="view-toggle" id="scheduleViewToggle">
      <button data-mode="simple" class="${scheduleViewMode==='simple'?'active':''}">Simple</button>
      <button data-mode="odds" class="${scheduleViewMode==='odds'?'active':''}">Odds Compare</button>
      <button data-mode="marketlab" class="${scheduleViewMode==='marketlab'?'active':''}">Market Lab</button>
      <button data-mode="results" class="${scheduleViewMode==='results'?'active':''}">Results</button>
    </div>
      ${scheduleViewMode === 'marketlab' ? `
      <div class="view-toggle marketlab-sub-toggle" id="marketLabSubToggle">
        <button onclick="setMarketLabMode('spreads')" class="${scheduleMarketLabMode==='spreads'?'active':''}">Spreads</button>
        <button onclick="setMarketLabMode('totals')" class="${scheduleMarketLabMode==='totals'?'active':''}">Totals</button>
      </div>` : ''}
    <div id="scheduleFilterStrip" class="schedule-filter-strip" style="margin-top:12px">
      <select id="fWeek"><option value="all">All weeks</option>${weeks.map(w=>`<option value="${w}">Week ${w}</option>`).join('')}</select>
      <select id="fConf"><option value="all">All conferences</option>${DB.conferences.map(c=>`<option value="${c.conference}">${c.conference}</option>`).join('')}</select>
      <input id="fTeam" placeholder="Filter team">
      <select id="fType"><option value="all">All games</option><option value="conference">Conference only</option><option value="neutral">Neutral only</option><option value="final">Final only</option><option value="open">Open only</option></select>
    </div>
    <div id="scheduleWrap"></div>
  `;
}
function drawScheduleTableFromCurrentFilters() {
  const weekEl = byId('fWeek'), confEl = byId('fConf'), teamEl = byId('fTeam'), typeEl = byId('fType'), wrap = byId('scheduleWrap');
  if (!weekEl || !confEl || !teamEl || !typeEl || !wrap) return;
  const week = weekEl.value;
  const conf = confEl.value;
  const team = teamEl.value.trim().toLowerCase();
  const type = typeEl.value;
  let games = DB.games.filter(g => week==='all' || String(g.week)===String(week));
  if (conf!=='all') games = games.filter(g => g.home_conference===conf || g.away_conference===conf);
  if (team) games = games.filter(g => g.home_team.toLowerCase().includes(team) || g.away_team.toLowerCase().includes(team));
  if (type==='conference') games = games.filter(g => g.is_conference_game);
  if (type==='neutral') games = games.filter(g => g.neutral_site);
  if (type==='final') games = games.filter(g => gameState(g).status === 'final');
  if (type==='open') games = games.filter(g => gameState(g).status !== 'final');
  wrap.innerHTML = scheduleTable(games, scheduleViewMode);
}
function mountScheduleFilters() {
  ['fWeek','fConf','fTeam','fType'].forEach(id => byId(id).addEventListener('input', drawScheduleTableFromCurrentFilters));
  const toggle = byId('scheduleViewToggle');
  if (toggle) toggle.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {
    scheduleViewMode = btn.dataset.mode;
    localStorage.setItem('ncaaf_2026_schedule_view_mode_v1', scheduleViewMode);
    toggle.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.mode === scheduleViewMode));
    drawScheduleTableFromCurrentFilters();
  }));
  drawScheduleTableFromCurrentFilters();
}


function rankValue(value, rank, suffix='') {
  return `${value} <span class="small">(#${rank ?? '—'}${suffix})</span>`;
}
const rankSortLabels = {
  rank: 'Rank', team: 'Team', conference: 'Conference', combo: 'Power Rating', sp_offense: 'SP Off', sp_defense: 'SP Def', hfa: 'HFA', overall_sos: 'OVR SOS', conf_sos: 'CONF SOS', avg_total_wins: 'Avg Wins'
};
let rankSortState = {key:'rank', dir:'asc'};
function rankSortValue(t, key) {
  if (key === 'team') return (t.team || '').toLowerCase();
  if (key === 'conference') return (t.conference || '').toLowerCase();
  if (key === 'overall_sos') return overallSOSByTeam[t.team];
  if (key === 'conf_sos') return confSOSByTeam[t.team];
  return t[key];
}
function sortedRankTeams() {
  const {key, dir} = rankSortState;
  const mult = dir === 'asc' ? 1 : -1;
  return [...DB.teams].sort((a,b) => {
    let av = rankSortValue(a, key), bv = rankSortValue(b, key);
    const aMissing = av === undefined || av === null || Number.isNaN(av);
    const bMissing = bv === undefined || bv === null || Number.isNaN(bv);
    if (aMissing && bMissing) return a.rank - b.rank;
    if (aMissing) return 1;
    if (bMissing) return -1;
    if (typeof av === 'string' || typeof bv === 'string') {
      const cmp = String(av).localeCompare(String(bv));
      return cmp !== 0 ? cmp * mult : a.rank - b.rank;
    }
    if (av === bv) return a.rank - b.rank;
    return (av - bv) * mult;
  });
}
function sortArrow(key) {
  return rankSortState.key === key ? `<span class="sort-arrow">${rankSortState.dir === 'asc' ? '▲' : '▼'}</span>` : '';
}
function sortableTh(key, label) {
  return `<th class="sortable" onclick="setRankSort('${key}')">${label}${sortArrow(key)}</th>`;
}
function setRankSort(key) {
  if (rankSortState.key === key) rankSortState.dir = rankSortState.dir === 'asc' ? 'desc' : 'asc';
  else {
    rankSortState.key = key;
    rankSortState.dir = (key === 'team' || key === 'conference' || key === 'rank' || key === 'sp_defense') ? 'asc' : 'desc';
  }
  if ((location.hash || '#/') !== '#rankings') location.hash = '#rankings';
  else route();
}
function mountRankSortControls() {
  const select = byId('rankSortSelect');
  const dirBtn = byId('rankSortDirBtn');
  if (!select || !dirBtn) return;
  select.value = rankSortState.key;
  dirBtn.textContent = rankSortState.dir === 'asc' ? 'Ascending' : 'Descending';
  select.addEventListener('change', e => setRankSort(e.target.value));
  dirBtn.addEventListener('click', () => { rankSortState.dir = rankSortState.dir === 'asc' ? 'desc' : 'asc'; route(); });
}


const RETURNING_PRODUCTION_2026 = {"Notre Dame":{"rank":1,"overall":72,"off":67,"offRank":19,"def":77,"defRank":2},"Maryland":{"rank":2,"overall":71,"off":68,"offRank":17,"def":74,"defRank":4},"Nebraska":{"rank":3,"overall":69,"off":69,"offRank":14,"def":69,"defRank":7},"Virginia Tech":{"rank":4,"overall":69,"off":71,"offRank":9,"def":67,"defRank":8},"South Carolina":{"rank":5,"overall":68,"off":76,"offRank":2,"def":61,"defRank":30},"Texas":{"rank":6,"overall":68,"off":73,"offRank":4,"def":63,"defRank":19},"Minnesota":{"rank":7,"overall":68,"off":71,"offRank":10,"def":65,"defRank":12},"Georgia":{"rank":8,"overall":68,"off":63,"offRank":32,"def":72,"defRank":5},"UCLA":{"rank":9,"overall":67,"off":73,"offRank":5,"def":61,"defRank":29},"Florida":{"rank":10,"overall":66,"off":55,"offRank":66,"def":77,"defRank":1},"Oregon":{"rank":11,"overall":66,"off":65,"offRank":26,"def":66,"defRank":11},"Texas Tech":{"rank":12,"overall":65,"off":67,"offRank":20,"def":64,"defRank":17},"USC":{"rank":13,"overall":65,"off":67,"offRank":22,"def":64,"defRank":16},"Texas A&M":{"rank":14,"overall":65,"off":67,"offRank":21,"def":63,"defRank":18},"Washington":{"rank":15,"overall":65,"off":69,"offRank":13,"def":61,"defRank":27},"Oklahoma":{"rank":16,"overall":65,"off":75,"offRank":3,"def":55,"defRank":57},"Houston":{"rank":17,"overall":65,"off":71,"offRank":7,"def":58,"defRank":44},"BYU":{"rank":18,"overall":64,"off":59,"offRank":50,"def":69,"defRank":6},"Florida Atlantic":{"rank":19,"overall":64,"off":62,"offRank":34,"def":65,"defRank":14},"Michigan":{"rank":20,"overall":63,"off":72,"offRank":6,"def":55,"defRank":55},"New Mexico":{"rank":21,"overall":63,"off":68,"offRank":16,"def":58,"defRank":40},"SMU":{"rank":22,"overall":62,"off":66,"offRank":23,"def":58,"defRank":38},"Tulsa":{"rank":23,"overall":62,"off":64,"offRank":28,"def":60,"defRank":36},"Eastern Michigan":{"rank":24,"overall":62,"off":59,"offRank":52,"def":64,"defRank":15},"Delaware":{"rank":25,"overall":62,"off":62,"offRank":38,"def":62,"defRank":24},"Tennessee":{"rank":26,"overall":62,"off":58,"offRank":53,"def":65,"defRank":13},"Syracuse":{"rank":27,"overall":62,"off":56,"offRank":63,"def":67,"defRank":9},"Ole Miss":{"rank":28,"overall":61,"off":61,"offRank":42,"def":62,"defRank":25},"Central Florida":{"rank":29,"overall":61,"off":61,"offRank":41,"def":60,"defRank":37},"LSU":{"rank":30,"overall":61,"off":61,"offRank":43,"def":60,"defRank":35},"Ohio State":{"rank":31,"overall":60,"off":71,"offRank":8,"def":50,"defRank":78},"Arizona":{"rank":32,"overall":60,"off":66,"offRank":24,"def":55,"defRank":56},"Stanford":{"rank":33,"overall":60,"off":58,"offRank":54,"def":62,"defRank":21},"SDSU":{"rank":34,"overall":59,"off":76,"offRank":1,"def":43,"defRank":100},"Wisconsin":{"rank":35,"overall":59,"off":61,"offRank":45,"def":57,"defRank":46},"Virginia":{"rank":36,"overall":59,"off":55,"offRank":65,"def":62,"defRank":20},"Air Force":{"rank":37,"overall":59,"off":42,"offRank":108,"def":75,"defRank":3},"Kansas State":{"rank":38,"overall":58,"off":65,"offRank":25,"def":51,"defRank":73},"Kansas":{"rank":39,"overall":58,"off":49,"offRank":79,"def":67,"defRank":10},"Purdue":{"rank":40,"overall":58,"off":61,"offRank":40,"def":55,"defRank":58},"Pittsburgh":{"rank":41,"overall":58,"off":60,"offRank":49,"def":56,"defRank":49},"Oklahoma State":{"rank":42,"overall":58,"off":62,"offRank":35,"def":53,"defRank":65},"California":{"rank":43,"overall":58,"off":70,"offRank":11,"def":45,"defRank":90},"Northwestern":{"rank":44,"overall":57,"off":57,"offRank":59,"def":58,"defRank":43},"Boise State":{"rank":45,"overall":57,"off":60,"offRank":46,"def":55,"defRank":60},"Auburn":{"rank":46,"overall":57,"off":56,"offRank":62,"def":58,"defRank":41},"Jacksonville State":{"rank":47,"overall":57,"off":60,"offRank":47,"def":54,"defRank":62},"Florida State":{"rank":48,"overall":57,"off":57,"offRank":58,"def":57,"defRank":47},"Liberty":{"rank":49,"overall":57,"off":64,"offRank":29,"def":50,"defRank":77},"Cincinnati":{"rank":50,"overall":57,"off":57,"offRank":57,"def":56,"defRank":50},"Texas State":{"rank":51,"overall":56,"off":70,"offRank":12,"def":43,"defRank":98},"Indiana":{"rank":52,"overall":56,"off":54,"offRank":69,"def":58,"defRank":39},"Louisiana Tech":{"rank":53,"overall":56,"off":64,"offRank":30,"def":48,"defRank":82},"Utah":{"rank":54,"overall":55,"off":55,"offRank":64,"def":55,"defRank":53},"Colorado":{"rank":55,"overall":55,"off":57,"offRank":60,"def":53,"defRank":66},"Arkansas":{"rank":56,"overall":55,"off":55,"offRank":67,"def":55,"defRank":59},"UTSA":{"rank":57,"overall":54,"off":64,"offRank":27,"def":44,"defRank":93},"NC State":{"rank":58,"overall":54,"off":62,"offRank":39,"def":46,"defRank":84},"Clemson":{"rank":59,"overall":53,"off":46,"offRank":94,"def":61,"defRank":26},"Louisville":{"rank":60,"overall":53,"off":52,"offRank":73,"def":55,"defRank":61},"Baylor":{"rank":61,"overall":53,"off":44,"offRank":102,"def":62,"defRank":22},"Wake Forest":{"rank":62,"overall":53,"off":45,"offRank":96,"def":61,"defRank":33},"Fresno St.":{"rank":63,"overall":53,"off":52,"offRank":76,"def":54,"defRank":64},"Temple":{"rank":64,"overall":53,"off":62,"offRank":37,"def":43,"defRank":96},"North Dakota State":{"rank":65,"overall":52,"off":45,"offRank":97,"def":60,"defRank":34},"West Virginia":{"rank":66,"overall":52,"off":57,"offRank":55,"def":46,"defRank":86},"Penn State":{"rank":67,"overall":52,"off":50,"offRank":78,"def":53,"defRank":67},"UL-Monroe":{"rank":68,"overall":51,"off":63,"offRank":33,"def":40,"defRank":106},"TCU":{"rank":69,"overall":51,"off":44,"offRank":100,"def":58,"defRank":42},"Arizona State":{"rank":70,"overall":51,"off":53,"offRank":70,"def":49,"defRank":79},"Western Michigan":{"rank":71,"overall":51,"off":60,"offRank":48,"def":42,"defRank":103},"New Mexico State":{"rank":72,"overall":51,"off":46,"offRank":93,"def":55,"defRank":54},"Boston College":{"rank":73,"overall":50,"off":44,"offRank":101,"def":57,"defRank":48},"Army":{"rank":74,"overall":50,"off":67,"offRank":18,"def":33,"defRank":127},"Illinois":{"rank":75,"overall":50,"off":52,"offRank":74,"def":47,"defRank":83},"Missouri":{"rank":76,"overall":49,"off":59,"offRank":51,"def":40,"defRank":107},"Duke":{"rank":77,"overall":49,"off":48,"offRank":87,"def":51,"defRank":72},"Miami-FL":{"rank":78,"overall":49,"off":48,"offRank":85,"def":51,"defRank":74},"Georgia Tech":{"rank":79,"overall":49,"off":37,"offRank":117,"def":61,"defRank":28},"Sam Houston State":{"rank":80,"overall":49,"off":52,"offRank":71,"def":46,"defRank":87},"UL-Lafayette":{"rank":81,"overall":49,"off":63,"offRank":31,"def":35,"defRank":125},"Arkansas State":{"rank":82,"overall":49,"off":52,"offRank":72,"def":45,"defRank":89},"Kennesaw State":{"rank":83,"overall":49,"off":42,"offRank":107,"def":55,"defRank":51},"Miami-OH":{"rank":84,"overall":49,"off":45,"offRank":95,"def":52,"defRank":68},"Northern Illinois":{"rank":85,"overall":48,"off":68,"offRank":15,"def":28,"defRank":132},"Mississippi State":{"rank":86,"overall":48,"off":44,"offRank":99,"def":52,"defRank":69},"Kent State":{"rank":87,"overall":48,"off":57,"offRank":56,"def":39,"defRank":108},"Marshall":{"rank":88,"overall":48,"off":61,"offRank":44,"def":36,"defRank":123},"Utah State":{"rank":89,"overall":48,"off":40,"offRank":110,"def":55,"defRank":52},"Alabama":{"rank":90,"overall":48,"off":35,"offRank":119,"def":61,"defRank":32},"Nevada":{"rank":91,"overall":48,"off":57,"offRank":61,"def":39,"defRank":109},"Rutgers":{"rank":92,"overall":47,"off":49,"offRank":82,"def":46,"defRank":88},"Navy":{"rank":93,"overall":47,"off":33,"offRank":121,"def":61,"defRank":31},"Oregon State":{"rank":94,"overall":47,"off":49,"offRank":80,"def":44,"defRank":92},"FIU":{"rank":95,"overall":47,"off":43,"offRank":105,"def":50,"defRank":76},"Massachusetts":{"rank":96,"overall":46,"off":49,"offRank":81,"def":43,"defRank":97},"Michigan State":{"rank":97,"overall":46,"off":48,"offRank":88,"def":45,"defRank":91},"Kentucky":{"rank":98,"overall":46,"off":40,"offRank":112,"def":52,"defRank":70},"Colorado State":{"rank":99,"overall":46,"off":38,"offRank":116,"def":54,"defRank":63},"Central Michigan":{"rank":100,"overall":46,"off":62,"offRank":36,"def":29,"defRank":131},"Hawaii":{"rank":101,"overall":45,"off":54,"offRank":68,"def":37,"defRank":118},"Iowa State":{"rank":102,"overall":45,"off":44,"offRank":104,"def":46,"defRank":85},"North Carolina":{"rank":103,"overall":44,"off":47,"offRank":91,"def":42,"defRank":102},"Iowa":{"rank":104,"overall":44,"off":48,"offRank":84,"def":40,"defRank":105},"South Alabama":{"rank":105,"overall":44,"off":51,"offRank":77,"def":37,"defRank":116},"Vanderbilt":{"rank":106,"overall":44,"off":38,"offRank":115,"def":49,"defRank":80},"Charlotte":{"rank":107,"overall":43,"off":52,"offRank":75,"def":34,"defRank":126},"Georgia Southern":{"rank":108,"overall":43,"off":23,"offRank":134,"def":62,"defRank":23},"Washington State":{"rank":109,"overall":42,"off":48,"offRank":86,"def":36,"defRank":121},"East Carolina":{"rank":110,"overall":42,"off":33,"offRank":122,"def":50,"defRank":75},"Memphis":{"rank":111,"overall":42,"off":44,"offRank":98,"def":39,"defRank":110},"Coastal Carolina":{"rank":112,"overall":42,"off":39,"offRank":114,"def":44,"defRank":94},"USF":{"rank":113,"overall":41,"off":47,"offRank":90,"def":36,"defRank":122},"Old Dominion":{"rank":114,"overall":40,"off":23,"offRank":136,"def":58,"defRank":45},"Akron":{"rank":115,"overall":40,"off":44,"offRank":103,"def":37,"defRank":119},"UNLV":{"rank":116,"overall":40,"off":40,"offRank":111,"def":40,"defRank":104},"Tulane":{"rank":117,"overall":40,"off":28,"offRank":127,"def":52,"defRank":71},"Wyoming":{"rank":118,"overall":40,"off":43,"offRank":106,"def":36,"defRank":120},"Troy":{"rank":119,"overall":39,"off":47,"offRank":92,"def":32,"defRank":129},"Rice":{"rank":120,"overall":39,"off":40,"offRank":113,"def":38,"defRank":113},"Georgia State":{"rank":121,"overall":38,"off":48,"offRank":83,"def":27,"defRank":133},"Middle Tennessee":{"rank":122,"overall":36,"off":34,"offRank":120,"def":37,"defRank":115},"Ball State":{"rank":123,"overall":36,"off":47,"offRank":89,"def":24,"defRank":136},"Bowling Green":{"rank":124,"overall":35,"off":32,"offRank":124,"def":38,"defRank":112},"UAB":{"rank":125,"overall":35,"off":32,"offRank":123,"def":38,"defRank":114},"UTEP":{"rank":126,"overall":35,"off":27,"offRank":129,"def":43,"defRank":99},"Appalachian State":{"rank":127,"overall":34,"off":30,"offRank":125,"def":39,"defRank":111},"Missouri State":{"rank":128,"overall":34,"off":25,"offRank":132,"def":44,"defRank":95},"Ohio":{"rank":129,"overall":33,"off":18,"offRank":138,"def":48,"defRank":81},"Toledo":{"rank":130,"overall":33,"off":42,"offRank":109,"def":25,"defRank":135},"Sacramento State":{"rank":131,"overall":32,"off":21,"offRank":137,"def":42,"defRank":101},"North Texas":{"rank":132,"overall":32,"off":28,"offRank":126,"def":35,"defRank":124},"Western Kentucky":{"rank":133,"overall":32,"off":37,"offRank":118,"def":26,"defRank":134},"Connecticut":{"rank":134,"overall":31,"off":25,"offRank":131,"def":37,"defRank":117},"Buffalo":{"rank":135,"overall":30,"off":26,"offRank":130,"def":33,"defRank":128},"James Madison":{"rank":136,"overall":30,"off":27,"offRank":128,"def":32,"defRank":130},"San Jose State":{"rank":137,"overall":24,"off":24,"offRank":133,"def":23,"defRank":137},"Southern Miss":{"rank":138,"overall":22,"off":23,"offRank":135,"def":20,"defRank":138}};

function normReturningProdTeamName(name) {
  return String(name || '')
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '');
}

const returningProdByNormTeam = Object.fromEntries(
  Object.entries(RETURNING_PRODUCTION_2026).map(([team, data]) => [normReturningProdTeamName(team), data])
);

function returningProductionRows(teamName) {
  const rp = RETURNING_PRODUCTION_2026[teamName] || returningProdByNormTeam[normReturningProdTeamName(teamName)];
  if (!rp) return '';
  return `
    ${ratingRow('Returning Prod', rp.overall, rp.rank, '%')}
    ${ratingRow('Returning Prod Off', rp.off, rp.offRank, '%')}
    ${ratingRow('Returning Prod Def', rp.def, rp.defRank, '%')}
  `;
}


function equalWeightTestCell(teamName) {
  const r = EQUAL_WEIGHT_TEST_RATINGS[teamName];
  if (!r) return '<span class="muted">—</span>';
  const partial = r.source_count < 5;
  const title = partial ? ` title="Partial test coverage: missing ${r.missing_sources}"` : '';
  return `<div class="test-rating-cell"${title}>
    <span class="test-rating-main">${Number(r.rating).toFixed(1)}</span>
    <span class="test-rating-rank">#${r.rank}${partial ? ` · ${r.source_count}/5` : ''}</span>
  </div>`;
}


let ratingLabRanksCache = null;
function ratingLabSystems() {
  return ['spplus','fpi','teamrankings','kford','bradpowers'];
}
function ratingLabLabel(s) {
  return (RATING_SOURCE_STATUS[s] && RATING_SOURCE_STATUS[s].label) || s;
}
function getRatingLabWeights() {
  try {
    const saved = JSON.parse(localStorage.getItem('ratingLabWeights') || '{}');
    return Object.assign({}, DEFAULT_RATING_WEIGHTS, saved);
  } catch(e) {
    return Object.assign({}, DEFAULT_RATING_WEIGHTS);
  }
}
function saveRatingLabWeights(w) {
  ratingLabRanksCache = null;
  localStorage.setItem('ratingLabWeights', JSON.stringify(w));
}
function resetRatingLabWeights() {
  ratingLabRanksCache = null;
  localStorage.setItem('ratingLabOpen', '1');
  localStorage.removeItem('ratingLabWeights');
  route();
}
function normalizeRatingLabWeights() {
  const w = getRatingLabWeights();
  const systems = ratingLabSystems();
  const total = systems.reduce((sum,s)=>sum + Number(w[s] || 0), 0);
  if (!total) return;
  systems.forEach(s => w[s] = Number(w[s] || 0) / total);
  saveRatingLabWeights(w);
  route();
}
function setRatingLabWeight(system, pct) {
  const w = getRatingLabWeights();
  w[system] = Math.max(0, Number(pct || 0)) / 100;
  saveRatingLabWeights(w);
  route();
}
function calcRatingLab(teamName) {
  const vals = RATING_SOURCE_VALUES[teamName] || {};
  const w = getRatingLabWeights();
  let num = 0, den = 0, count = 0, missing = [];
  ratingLabSystems().forEach(s => {
    const v = vals[s];
    const wt = Number(w[s] || 0);
    if (v == null || !Number.isFinite(Number(v))) {
      if (wt > 0) missing.push(s);
      return;
    }
    if (wt > 0) {
      num += Number(v) * wt;
      den += wt;
    }
    count++;
  });
  if (!den) return {rating:null, source_count:count, missing_sources:missing};
  return {rating:num/den, source_count:count, missing_sources:missing};
}
function ratingLabRanks() {
  if (ratingLabRanksCache) return ratingLabRanksCache;
  const rows = Object.keys(RATING_SOURCE_VALUES).map(team => {
    const r = calcRatingLab(team);
    return {team, rating:r.rating};
  }).filter(x => x.rating != null).sort((a,b)=>b.rating-a.rating);
  const out = {};
  rows.forEach((x,i)=>out[x.team] = i + 1);
  ratingLabRanksCache = out;
  return out;
}
function equalWeightTestCell(teamName) {
  const r = calcRatingLab(teamName);
  if (r.rating == null) return '<span class="muted">—</span>';
  const ranks = ratingLabRanks();
  const vals = RATING_SOURCE_VALUES[teamName] || {};
  const w = getRatingLabWeights();
  const detailRows = ratingLabSystems().map(s => {
    const v = vals[s];
    const pct = Math.round(Number(w[s] || 0) * 100);
    const st = RATING_SOURCE_STATUS[s] || {};
    return `<tr>
      <td>${ratingLabLabel(s)}</td>
      <td>${v == null ? '—' : Number(v).toFixed(1)}</td>
      <td>${pct}%</td>
      <td>${st.updated ? `File Updated: ${st.updated}` : '—'}</td>
    </tr>`;
  }).join('');
  const partial = r.source_count < ratingLabSystems().length;
  return `<details class="test-rating-detail">
    <summary>
      <span class="test-rating-cell">
        <span class="test-rating-main">${Number(r.rating).toFixed(1)}</span>
        <span class="test-rating-rank">#${ranks[teamName] || '—'}${partial ? ` · ${r.source_count}/5` : ''}</span>
      </span>
    </summary>
    <table class="source-detail-table"><tbody>
      <tr><th>Source</th><th>Rating</th><th>Wt</th><th>Updated</th></tr>
      ${detailRows}
    </tbody></table>
  </details>`;
}
function applyRatingLabDraftWeights() {
  const w = {};
  let totalPct = 0;
  ratingLabSystems().forEach(s => {
    const input = document.getElementById(`ratingLabInput_${s}`);
    const slider = document.getElementById(`ratingLabSlider_${s}`);
    const pct = Math.max(0, Number(input ? input.value : (slider ? slider.value : 0)));
    totalPct += pct;
    w[s] = pct / 100;
  });
  if (Math.round(totalPct) !== 100) {
    alert(`Weights must total 100% before applying. Current total: ${Math.round(totalPct)}%. Use "Scale Draft to 100%" or adjust sliders.`);
    return;
  }
  localStorage.setItem('ratingLabOpen', '1');
  saveRatingLabWeights(w);
  route();
}
function scaleRatingLabDraftTo100() {
  let total = 0;
  const vals = {};
  ratingLabSystems().forEach(s => {
    const input = document.getElementById(`ratingLabInput_${s}`);
    const slider = document.getElementById(`ratingLabSlider_${s}`);
    const v = Math.max(0, Number(input ? input.value : (slider ? slider.value : 0)));
    vals[s] = v;
    total += v;
  });
  if (!total) {
    alert('Draft weights total 0%. Move at least one slider above 0 first.');
    return;
  }
  let rounded = {};
  let used = 0;
  ratingLabSystems().forEach((s, idx) => {
    if (idx === ratingLabSystems().length - 1) {
      rounded[s] = Math.max(0, 100 - used);
    } else {
      rounded[s] = Math.round(vals[s] / total * 100);
      used += rounded[s];
    }
  });
  ratingLabSystems().forEach(s => {
    const slider = document.getElementById(`ratingLabSlider_${s}`);
    const input = document.getElementById(`ratingLabInput_${s}`);
    const out = document.getElementById(`ratingLabPct_${s}`);
    if (slider) slider.value = rounded[s];
    if (input) input.value = rounded[s];
    if (out) out.textContent = rounded[s] + '%';
  });
  updateRatingLabDraftTotal();
}
function setRatingLabDraftPct(system, value) {
  let pct = Number(value);
  if (!Number.isFinite(pct)) pct = 0;
  pct = Math.max(0, Math.min(100, Math.round(pct)));

  const slider = document.getElementById(`ratingLabSlider_${system}`);
  const input = document.getElementById(`ratingLabInput_${system}`);
  const out = document.getElementById(`ratingLabPct_${system}`);

  if (slider) slider.value = pct;
  if (input) input.value = pct;
  if (out) out.textContent = pct + '%';

  updateRatingLabDraftTotal();
}
function updateRatingLabDraftTotal() {
  let total = 0;
  ratingLabSystems().forEach(s => {
    const input = document.getElementById(`ratingLabInput_${s}`);
    const slider = document.getElementById(`ratingLabSlider_${s}`);
    const pct = Number(input ? input.value : (slider ? slider.value : 0));
    total += pct;
    const out = document.getElementById(`ratingLabPct_${s}`);
    if (out) out.textContent = pct + '%';
  });
  const t = document.getElementById('ratingLabDraftTotal');
  if (t) {
    t.textContent = total + '%';
    t.className = total === 100 ? 'ok-total' : 'bad-total';
  }
}
function ratingsWeightLabPanel() {
  const w = getRatingLabWeights();
  const officialTotal = ratingLabSystems().reduce((sum,s)=>sum + Number(DEFAULT_RATING_WEIGHTS[s] || 0), 0);
  const labTotal = ratingLabSystems().reduce((sum,s)=>sum + Number(w[s] || 0), 0);
  const rows = ratingLabSystems().map(s => {
    const pct = Math.round(Number(w[s] || 0) * 100);
    const defaultPct = Math.round(Number(DEFAULT_RATING_WEIGHTS[s] || 0) * 100);
    const st = RATING_SOURCE_STATUS[s] || {};
    return `<div class="rating-weight-row compact">
      <div class="rating-weight-label">
        <b>${ratingLabLabel(s)}</b>
        <span>${pct}% custom · ${defaultPct}% default · File Updated: ${st.updated || 'No file'} · ${st.status || ''}</span>
      </div>
      <div class="rating-weight-controls">
        <input id="ratingLabSlider_${s}" type="range" min="0" max="100" value="${pct}" oninput="setRatingLabDraftPct('${s}', this.value)">
        <input id="ratingLabInput_${s}" class="rating-weight-input" type="number" min="0" max="100" step="1" value="${pct}" oninput="setRatingLabDraftPct('${s}', this.value)">
      </div>
      <div id="ratingLabPct_${s}" class="rating-weight-pct">${pct}%</div>
    </div>`;
  }).join('');
  const isOpen = localStorage.getItem('ratingLabOpen') === '1';
  return `<details id="ratingsWeightLab" class="card ratings-weight-lab compact" ${isOpen ? 'open' : ''} ontoggle="localStorage.setItem('ratingLabOpen', this.open ? '1' : '0')">
    <summary>
      <div>
        <b>Rating Weights</b>
        <span class="small muted">Official/default: ${ratingLabDefaultWeightSummaryText()} · click to expand</span>
      </div>
      <span class="rating-lab-summary-pill">Click to expand · Custom ${Math.round(labTotal*100)}% · Default ${Math.round(officialTotal*100)}%</span>
    </summary>
    <div class="small muted rating-lab-note">Custom weights on this page are display-only unless ratings_config.json is changed and the site is rebuilt.</div>
    <div class="rating-weight-total">Draft total: <span id="ratingLabDraftTotal">${Math.round(labTotal*100)}%</span></div>
    ${rows}
    <div class="rating-weight-actions">
      <button class="pill" onclick="applyRatingLabDraftWeights()">Apply Weights</button>
      <button class="pill" onclick="scaleRatingLabDraftTo100()">Scale Draft to 100%</button>
      <button class="pill" onclick="resetRatingLabWeights()">Reset to Default</button>
    </div>
  </details>`;
}
function mountRatingsLabPanel() { return; }


function rankingsPowerRatingTh(key, label) {
  const note = ratingLabWeightsAreDefault() ? 'Default weights' : `Lab: ${ratingLabWeightSummaryText()}`;
  return `<th class="sortable rankings-power-th" onclick="setRankSort('${key}')">
    <div>${label}${sortArrow(key)}</div>
    <div class="rankings-power-weight-note">${note}</div>
  </th>`;
}
function rankingsPowerRatingCell(t) {
  const useLab = !ratingLabWeightsAreDefault();
  if (!useLab) return rankValueColored(t.combo.toFixed(1), comboRankByTeam[t.team]);

  const r = calcRatingLab(t.team);
  const ranks = ratingLabRanks();
  if (!r || r.rating == null) return rankValueColored(t.combo.toFixed(1), comboRankByTeam[t.team]);

  return `<div class="rankings-power-cell">
    <div>${rankValueColored(Number(r.rating).toFixed(1), ranks[t.team])}</div>
    <div class="small muted">official: ${t.combo.toFixed(1)} (#${comboRankByTeam[t.team] || '—'})</div>
  </div>`;
}

function renderRankMobileCard(t) {
  const confSuffix = t.conference && t.conference !== 'Independent' ? ' conf' : '';
  return `<div class="rank-card">
    <div class="rank-card-head">
      <div>
        <div class="rank-card-title">${linkTeam(t.team)}</div>
        <div class="small">${linkConf(t.conference)}</div>
      </div>
      <div class="rank-card-rank">Rank #${t.rank}</div>
    </div>
    <div class="rank-card-grid">
      <div class="rank-stat"><div class="label">Power Rating</div><div class="value">${rankingsPowerRatingCell(t)}</div></div>
      <div class="rank-stat"><div class="label">Avg Wins</div><div class="value">${rankValueColored(t.avg_total_wins.toFixed(2), avgWinsRankByTeam[t.team])}</div></div>
      <div class="rank-stat"><div class="label">OVR SOS</div><div class="value">${rankValueColored(fmtSOS(overallSOSByTeam[t.team]), overallSOSRankByTeam[t.team], '', true, 138)}</div></div>
      <div class="rank-stat"><div class="label">CONF SOS</div><div class="value">${rankValue(fmtSOS(confSOSByTeam[t.team]), confSOSRankByTeam[t.team], confSuffix)}</div></div>
      <div class="rank-stat"><div class="label">SP Off</div><div class="value">${rankValueColored(t.sp_offense.toFixed(1), spOffRankByTeam[t.team])}</div></div>
      <div class="rank-stat"><div class="label">SP Def</div><div class="value">${rankValueColored(t.sp_defense.toFixed(1), spDefRankByTeam[t.team])}</div></div>
      <div class="rank-stat"><div class="label">HFA</div><div class="value">${rankValueColored(t.hfa.toFixed(1), hfaRankByTeam[t.team])}</div></div>
      <div class="rank-stat"><div class="label">Conf Title</div><div class="value">${fmtPct(t.conference_title_pct)}</div></div>
    </div>
  </div>`;
}

function rankColorClass(rank, inverse=false, total=138) {
  const r = Number(rank);
  if (!Number.isFinite(r)) return 'rank-color-neutral';
  const pct = r / Number(total || 138);

  // Normal: #1 is best. Inverse: #1 is hardest/worst, useful for SOS.
  if (!inverse) {
    if (pct <= 0.25) return 'rank-color-good';
    if (pct <= 0.65) return 'rank-color-mid';
    return 'rank-color-bad';
  }
  if (pct <= 0.25) return 'rank-color-bad';
  if (pct <= 0.65) return 'rank-color-mid';
  return 'rank-color-good';
}

function rankValueColored(value, rank, suffix='', inverse=false, total=138) {
  const cls = rankColorClass(rank, inverse, total);
  return `<span class="rank-color ${cls}">${value} <span class="muted">(#${rank ?? '—'}${suffix})</span></span>`;
}

function renderRankings() {
  const rankTeams = sortedRankTeams();
  return `
    <div class="page-title">Rankings</div>
    <div class="page-sub">Laptop view keeps the full sortable table. Phone view switches to compact sortable team cards with the same rankings and SOS values.</div>
    <div class="mobile-actions">
      <a class="pill" href="#schedule">Schedule</a>
      <a class="pill" href="#conferences">Conferences</a>
    </div>
    <div class="rank-sort-controls">
      <select id="rankSortSelect">
        ${Object.entries(rankSortLabels).map(([key,label])=>`<option value="${key}">Sort by ${label}</option>`).join('')}
      </select>
      <button id="rankSortDirBtn" type="button">${rankSortState.dir === 'asc' ? 'Ascending' : 'Descending'}</button>
    </div>
    <div class="card desktop-rankings market-board-card" style="margin-top:16px">
      ${ratingsWeightLabPanel()}
    <table><thead><tr>${sortableTh('rank','Rank')}${sortableTh('team','Team')}${sortableTh('conference','Conference')}${rankingsPowerRatingTh('combo','Power Rating')}${sortableTh('sp_offense','SP Off')}${sortableTh('sp_defense','SP Def')}${sortableTh('hfa','HFA')}${sortableTh('overall_sos','OVR SOS')}${sortableTh('conf_sos','CONF SOS')}${sortableTh('avg_total_wins','Avg Wins')}</tr></thead><tbody>
      ${rankTeams.map(t=>`<tr><td>${t.rank}</td><td>${linkTeam(t.team)}</td><td>${linkConf(t.conference)}</td><td>${rankingsPowerRatingCell(t)}</td><td>${rankValueColored(t.sp_offense.toFixed(1), spOffRankByTeam[t.team])}</td><td>${rankValueColored(t.sp_defense.toFixed(1), spDefRankByTeam[t.team])}</td><td>${rankValueColored(t.hfa.toFixed(1), hfaRankByTeam[t.team])}</td><td>${rankValueColored(fmtSOS(overallSOSByTeam[t.team]), overallSOSRankByTeam[t.team], '', true, 138)}</td><td>${rankValueColored(fmtSOS(confSOSByTeam[t.team]), confSOSRankByTeam[t.team], t.conference && t.conference !== 'Independent' ? ' conf' : '', true, 18)}</td><td>${rankValueColored(t.avg_total_wins.toFixed(2), avgWinsRankByTeam[t.team])}</td></tr>`).join('')}
      </tbody></table>
    </div>
    <div class="card mobile-rankings" style="margin-top:12px">
      ${rankTeams.map(renderRankMobileCard).join('')}
    </div>
  `;
}


function allTeamObjects() {
  try {
    return Object.values(teamBySlug || {}).filter(Boolean);
  } catch (e) {
    return [];
  }
}
function conferenceTeamObjects(conf) {
  return allTeamObjects().filter(x => x && x.conference === conf);
}
function competitionRankByMetric(teamName, list, getter, desc=true) {
  const rows = (list || []).map(x => {
    const val = Number(getter(x));
    return {team:x.team, val};
  }).filter(x => Number.isFinite(x.val));

  rows.sort((a,b) => desc ? b.val - a.val : a.val - b.val);

  let rank = 0;
  let prev = null;
  for (let i = 0; i < rows.length; i++) {
    if (prev === null || rows[i].val !== prev) {
      rank = i + 1;
      prev = rows[i].val;
    }
    if (rows[i].team === teamName) return rank;
  }
  return null;
}
function currentRecordRank(teamName, confOnly=false) {
  const targetTeam = allTeamObjects().find(x => x.team === teamName);
  if (!targetTeam) return null;

  const list = confOnly ? conferenceTeamObjects(targetTeam.conference) : allTeamObjects();
  const stats = (getResultsSummary().teamStats || {});
  const targetStats = stats[teamName] || {wins:0, losses:0, conf_wins:0, conf_losses:0};

  const targetGames = confOnly
    ? Number(targetStats.conf_wins || 0) + Number(targetStats.conf_losses || 0)
    : Number(targetStats.wins || 0) + Number(targetStats.losses || 0);

  if (!targetGames) return null;

  const rows = list.map(x => {
    const s = stats[x.team] || {wins:0, losses:0, conf_wins:0, conf_losses:0};
    const wins = confOnly ? Number(s.conf_wins || 0) : Number(s.wins || 0);
    const losses = confOnly ? Number(s.conf_losses || 0) : Number(s.losses || 0);
    const games = wins + losses;
    if (!games) return {team:x.team, val:null};
    const pct = wins / games;
    return {team:x.team, val:(pct * 1000) + wins};
  }).filter(x => Number.isFinite(x.val));

  rows.sort((a,b) => b.val - a.val);

  let rank = 0;
  let prev = null;
  for (let i = 0; i < rows.length; i++) {
    if (prev === null || rows[i].val !== prev) {
      rank = i + 1;
      prev = rows[i].val;
    }
    if (rows[i].team === teamName) return rank;
  }
  return null;
}
function summaryToneClass(rank, total=138, invert=false) {
  const r = Number(rank);
  const t = Number(total) || 138;
  if (!Number.isFinite(r) || r <= 0) return 'summary-neutral';

  const pct = r / t;

  if (!invert) {
    if (pct <= 0.25) return 'summary-elite';
    if (pct <= 0.55) return 'summary-good';
    if (pct <= 0.80) return 'summary-mid';
    return 'summary-bad';
  }

  // For SOS, lower rank means harder schedule. Harder is colored red/yellow, easier green.
  if (pct <= 0.25) return 'summary-bad';
  if (pct <= 0.55) return 'summary-mid';
  if (pct <= 0.80) return 'summary-good';
  return 'summary-elite';
}
function summaryRankText(rank, total) {
  if (rank == null || rank === '' || rank === '—') return '';
  return `<span class="summary-rank summary-rank-under">#${rank}/${total}</span>`;
}
function miniSummary(label, value, rank=null, total=138, invert=false) {
  const tone = summaryToneClass(rank, total, invert);
  return `<div class="mini summary-kpi ${tone}">
    <div class="label">${label}</div>
    <div class="value">${value}${summaryRankText(rank, total)}</div>
  </div>`;
}


function numberOrNull(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}
function teamObjByNameSafe(name) {
  return teamByName[String(name || '').toLowerCase()] || null;
}
function gameHomeMargin(g, teamName) {
  const keys = [
    'proj_margin_home',
    'projected_margin_home',
    'margin_home',
    'pred_margin_home',
    'home_margin',
    'spread_home',
    'projected_spread_home'
  ];

  for (const k of keys) {
    const v = numberOrNull(g[k]);
    if (v !== null) return v;
  }

  const home = teamObjByNameSafe(g.home_team);
  const away = teamObjByNameSafe(g.away_team);
  if (!home || !away) return null;

  let margin = Number(home.combo) - Number(away.combo);
  if (!g.neutral_site) {
    margin += Number(home.hfa || 0);
  }
  return Number.isFinite(margin) ? margin : null;
}

function ratingLabValueForTeam(teamName) {
  const r = calcRatingLab(teamName);
  return r && r.rating != null && Number.isFinite(Number(r.rating)) ? Number(r.rating) : null;
}
function gameHomeMarginLab(g) {
  const home = teamObjByNameSafe(g.home_team);
  const away = teamObjByNameSafe(g.away_team);
  if (!home || !away) return null;

  const homeRating = ratingLabValueForTeam(g.home_team);
  const awayRating = ratingLabValueForTeam(g.away_team);

  if (homeRating == null || awayRating == null) return null;

  let margin = homeRating - awayRating;
  if (!g.neutral_site) {
    margin += Number(home.hfa || 0);
  }
  return Number.isFinite(margin) ? margin : null;
}
function spreadTextFromHomeMargin(g, homeMargin) {
  if (homeMargin == null || !Number.isFinite(Number(homeMargin))) return '—';
  const m = Number(homeMargin);
  if (Math.abs(m) < 0.05) return 'PK';
  const fav = m > 0 ? g.home_team : g.away_team;
  const abs = Math.abs(m).toFixed(1).replace(/\.0$/, '');
  return `${teamLabel(fav)} -${abs}`;
}
function labSpreadText(g) {
  return spreadTextFromHomeMargin(g, gameHomeMarginLab(g));
}
function labSpreadDiff(g) {
  const lab = gameHomeMarginLab(g);
  const official = Number(g.projected_margin_home);
  if (lab == null || !Number.isFinite(official)) return null;
  return lab - official;
}
function labSpreadCell(g) {
  const diff = labSpreadDiff(g);
  const cls = diff == null ? '' : (diff > 0 ? 'pos' : diff < 0 ? 'neg' : '');
  return `<div class="lab-spread-cell">
    <div class="line-main">${labSpreadText(g)}</div>
    <div class="small ${cls}">${diff == null ? 'vs official: —' : `vs official: ${fmtSigned(diff)}`}</div>
  </div>`;
}

function spreadForTeamText(g, teamName) {
  const homeMargin = gameHomeMargin(g, teamName);
  if (homeMargin === null) return '—';

  const isHome = g.home_team === teamName;
  const teamMargin = isHome ? homeMargin : -homeMargin;

  if (!Number.isFinite(teamMargin)) return '—';
  if (Math.abs(teamMargin) < 0.05) return 'PK';

  const abs = Math.abs(teamMargin).toFixed(1).replace(/\.0$/, '');
  return teamMargin > 0 ? `-${abs}` : `+${abs}`;
}
function keyGamesForTeam(teamName, games) {
  const scheduleRows = (games && games.length) ? games : gamesForTeam(teamName);

  return [...(scheduleRows || [])]
    .filter(g => g && g.week !== undefined)
    .map(g => {
      const isHome = g.home_team === teamName;
      const opp = isHome ? g.away_team : g.home_team;
      const oppObj = teamObjByNameSafe(opp);

      const homeMargin = gameHomeMargin(g, teamName);
      const teamMargin = homeMargin == null ? null : (isHome ? homeMargin : -homeMargin);

      const closeBonus = teamMargin == null ? 0 : Math.max(0, 10 - Math.abs(teamMargin));
      const confBonus = g.is_conference_game ? 5 : 0;
      const oppPower = Number(oppObj && oppObj.combo || 0);

      return {
        g,
        opp,
        oppObj,
        score: oppPower + confBonus + closeBonus,
        spread: spreadForTeamText(g, teamName)
      };
    })
    .sort((a,b) => b.score - a.score)
    .slice(0,3);
}

function renderKeyGamesHero(teamName, games) {
  const rows = keyGamesForTeam(teamName, games);

  return `<div class="key-games-hero">
    <div class="key-games-title">Key Games</div>
    <div class="key-games-grid">
      ${rows.length ? rows.map(x => {
        const g = x.g;
        const isHome = g.home_team === teamName;
        const loc = g.neutral_site ? 'Neutral' : (isHome ? 'Home' : 'Away');
        const date = g.date ? fmtDate(g.date) : `Week ${g.week}`;
        return `<div class="key-game-pill">
          <div class="key-game-top"><span>Wk ${g.week}</span><span>${date}</span></div>
          <div class="key-game-opp">${teamLabel(x.opp)}</div>
          <div class="key-game-bottom">
            <span class="key-game-loc">${loc}${g.is_conference_game ? ' · Conf' : ''}</span>
            <span class="key-spread-badge">${x.spread}</span>
          </div>
        </div>`;
      }).join('') : `<div class="small muted">No schedule rows found.</div>`}
    </div>
  </div>`;
}


function staffStatusClass(status) {
  const s = String(status || '').trim().toLowerCase();
  if (s === 'returning') return 'returning';
  if (s === 'new') return 'new';
  if (s === 'partial') return 'partial';
  return 'unverified';
}
function staffStatusText(status) {
  const s = String(status || '').trim().toLowerCase();
  if (s === 'returning') return 'Returning';
  if (s === 'new') return 'New';
  if (s === 'partial') return 'Partial';
  return 'Unverified';
}
function staffForTeam(teamName) {
  return STAFF_2026[teamName] || null;
}
function renderStaffHero(teamName) {
  const s = staffForTeam(teamName);
  if (!s) {
    return `<div class="staff-hero">
      <div class="staff-title">2026 Coaches</div>
      <div class="small muted">No staff import row mapped.</div>
    </div>`;
  }

  const record = s.record_2025 || '—';
  const confRecord = s.conf_record_2025 || '—';

  return `<div class="staff-hero">
    <div class="staff-title staff-title-inline">2026 Coaches</div>
    <div class="staff-row">
      <div class="staff-role">HC</div>
      <div class="staff-name">${escapeHtml(s.head_coach || '—')}</div>
      <div class="staff-status ${staffStatusClass(s.head_coach_status)}">${staffStatusText(s.head_coach_status)}</div>
    </div>
    <div class="staff-row">
      <div class="staff-role">OC</div>
      <div class="staff-name">${escapeHtml(s.offensive_coordinator || '—')}</div>
      <div class="staff-status ${staffStatusClass(s.oc_status)}">${staffStatusText(s.oc_status)}</div>
    </div>
    <div class="staff-row">
      <div class="staff-role">DC</div>
      <div class="staff-name">${escapeHtml(s.defensive_coordinator || '—')}</div>
      <div class="staff-status ${staffStatusClass(s.dc_status)}">${staffStatusText(s.dc_status)}</div>
    </div>
  </div>`;
}


function fmtProjectedRecord(wins, games) {
  const w = Number(wins);
  const g = Number(games);
  if (!Number.isFinite(w) || !Number.isFinite(g)) return '—';
  const losses = Math.max(0, g - w);
  return `${w.toFixed(1)}-${losses.toFixed(1)}`;
}


function renderTeamHeaderRecordLine(teamName) {
  const s = staffForTeam(teamName);
  if (!s) return '';
  const overall = s.record_2025 || '—';
  const conf = s.conf_record_2025 || '—';
  return `<div class="team-record-subline">
    <span>2025 Overall: <b>${escapeHtml(overall)}</b></span>
    <span>2025 Conf: <b>${escapeHtml(conf)}</b></span>
  </div>`;
}

function renderTeam(slug) {
  const t = teamBySlug[slug];
  if (!t) return `<div class="page-title">Team not found</div>`;
  const games = gamesForTeam(t.team);
  const confGames = games.filter(g => g.is_conference_game);
  const topDist = [...t.win_distribution].sort((a,b)=>a.wins-b.wins);
  return `
    <div class="hero team-hero">
      <div>
        <div class="team-title-row">
          <div class="page-title">${teamLabel(t.team)}</div>
          <div class="team-title-conf">${linkConf(t.conference)}</div>
        </div>
        ${renderTeamHeaderRecordLine(t.team)}
      </div>
      ${renderStaffHero(t.team)}
      ${renderKeyGamesHero(t.team, games)}
      <div class="hero-stats">
        ${(() => {
          const actual = getResultsSummary().teamStats[t.team] || {wins:0, losses:0, conf_wins:0, conf_losses:0};
          const allTeams = allTeamObjects();
          const confTeams = conferenceTeamObjects(t.conference);
          const allTotal = allTeams.length || 138;
          const confTotal = confTeams.length || 1;

          const actualRank = currentRecordRank(t.team, false);
          const confRecordRank = currentRecordRank(t.team, true);
          const projConfWinsRank = competitionRankByMetric(t.team, confTeams, x => x.avg_conference_wins, true);
          const makeTitleRank = competitionRankByMetric(t.team, confTeams, x => x.make_title_game_pct, true);
          const winConfRank = competitionRankByMetric(t.team, confTeams, x => x.conference_title_pct, true);

          return `
            ${miniSummary('2026 Record', `${actual.wins}-${actual.losses}`, actualRank, allTotal)}
            ${miniSummary('2026 Conf Record', `${actual.conf_wins}-${actual.conf_losses}`, confRecordRank, confTotal)}
            ${miniSummary('Power Rating', t.combo.toFixed(1), comboRankByTeam[t.team], allTotal)}
            ${miniSummary('Proj Record', fmtProjectedRecord(t.avg_total_wins, games.length), avgWinsRankByTeam[t.team], allTotal)}
            ${miniSummary('Proj Conf Record', fmtProjectedRecord(t.avg_conference_wins, confGames.length), projConfWinsRank, confTotal)}
            ${miniSummary('Overall SOS Adj', fmtSOS(overallSOSByTeam[t.team]), overallSOSRankByTeam[t.team], allTotal, true)}
            ${miniSummary('Conf SOS Adj', fmtSOS(confSOSByTeam[t.team]), confSOSRankByTeam[t.team], confTotal, true)}
            ${miniSummary('Win Conf %', fmtPct(t.conference_title_pct), winConfRank, confTotal)}
          `;
        })()}
      </div>
    </div>
    <div class="grid cols-3 team-dashboard-grid" style="margin-top:16px">
      ${renderTeamCoachCard(t.team)}
      ${renderMarketTeamCard(t.team)}
      

<div class="card ratings-card"><div class="section-title">Ratings</div><table class="compact-table"><thead><tr><th>Metric</th><th>Value</th><th>Rank</th></tr></thead><tbody>
        ${ratingRow('Power Rating', t.combo.toFixed(1), comboRankByTeam[t.team])}
        ${ratingTrendBlock(t.team)}
        ${ratingRow('SP Offense', t.sp_offense.toFixed(1), spOffRankByTeam[t.team])}
        ${ratingRow('SP Defense', t.sp_defense.toFixed(1), spDefRankByTeam[t.team])}
        ${ratingRow('Home Field', t.hfa.toFixed(1), hfaRankByTeam[t.team])}
        ${returningProductionRows(t.team)}
      </tbody></table></div>
      <div class="card win-distribution-card"><div class="section-title">Win Distribution</div>
        ${topDist.map(d=>`<div style="display:grid;grid-template-columns:34px 1fr 48px;gap:8px;align-items:center;margin:8px 0"><div>${d.wins}</div><div class="bar"><span style="width:${Math.max(2,d.probability*100)}%"></span></div><div class="small">${fmtPct(d.probability)}</div></div>`).join('')}
      </div>
      <div class="card conference-outlook-card"><div class="section-title">Conference Outlook</div>
        ${(() => {
          const actual = getResultsSummary().teamStats[t.team] || {wins:0, losses:0, conf_wins:0, conf_losses:0, pf:0, pa:0};
          return `
            <div class="small">Scheduled conference games: ${confGames.length}</div>
            <div class="small" style="margin-top:8px">Actual record: ${actual.wins}-${actual.losses}</div>
            <div class="small" style="margin-top:8px">Actual conf record: ${actual.conf_wins}-${actual.conf_losses}</div>
            <div class="small" style="margin-top:8px">Points for / against: ${actual.pf}-${actual.pa}</div>
            <div class="small" style="margin-top:8px">Overall SOS (venue-adjusted): ${fmtSOS(overallSOSByTeam[t.team])} (#${overallSOSRankByTeam[t.team] ?? '—'})</div>
            <div class="small" style="margin-top:8px">Conference SOS (venue-adjusted): ${fmtSOS(confSOSByTeam[t.team])} (#${confSOSRankByTeam[t.team] ?? '—'} in ${t.conference})</div>
            <div class="small" style="margin-top:8px">Make title game: ${fmtPct(t.make_title_game_pct)}</div>
            <div class="small" style="margin-top:8px">Win conference: ${fmtPct(t.conference_title_pct)}</div>
            <div class="small" style="margin-top:8px">Lose title game: ${fmtPct(t.lose_title_game_pct)}</div>
          `;
        })()}
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="section-title">Schedule</div>
      <table><thead><tr><th>Week</th><th>Date</th><th>Opponent</th><th>Location</th><th>Conf Gm</th><th>Opp Rank</th><th>Spread</th><th>Win %</th><th>Total</th><th>Status</th><th>Score</th><th>Result</th></tr></thead><tbody>
      ${(() => {
        const byWeek = new Map(games.map(g => [g.week, g]));
        const rows = [];
        for (let wk = 0; wk <= 13; wk++) {
          const g = byWeek.get(wk);
          if (!g) {
            rows.push(`<tr>
              <td>${wk}</td><td>—</td><td class="muted">Bye week</td><td>—</td>
              <td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td>
            </tr>`);
            continue;
          }
          const home = g.home_team===t.team;
          const opp = home ? g.away_team : g.home_team;
          const oppTeam = teamByName[opp.toLowerCase()];
          const winp = home ? g.win_prob_home : (1-g.win_prob_home);
          const st = gameState(g);
          let scoreTxt = '—', resultTxt = '—';
          if (st.status === 'final' && st.away_score !== '' && st.home_score !== '') {
            const ascore = Number(st.away_score), hscore = Number(st.home_score);
            scoreTxt = home ? `${hscore}-${ascore}` : `${ascore}-${hscore}`;
            if (ascore !== hscore) {
              const teamWon = home ? hscore > ascore : ascore > hscore;
              resultTxt = teamWon ? '<span class="pos">W</span>' : '<span class="neg">L</span>';
            } else {
              resultTxt = 'T';
            }
          }
          rows.push(`<tr>
            <td>${g.week}</td><td>${fmtDate(g.date)}</td><td>${linkTeam(opp)}</td><td>${g.neutral_site ? 'Neutral' : (home ? 'Home' : 'Away')}</td>
            <td>${g.is_conference_game ? 'Yes' : 'No'}</td><td>${oppTeam ? ('#'+oppTeam.rank) : '—'}</td><td>${scheduleSpreadCell(g)}</td><td>${(winp*100).toFixed(1)}%</td><td>${fmtProjectedTotalSafe(g.projected_total)}</td><td>${st.status === 'final' ? 'Final' : 'Scheduled'}</td><td>${scoreTxt}</td><td>${resultTxt}</td>
          </tr><tr class="matchup-detail-row"><td colspan="12">${matchupTeamScheduleBlock(g, t.team)}</td></tr>`);
        }
        return rows.join('');
      })()}
      </tbody></table>
    </div>
  `;
}

function fmtProjectedTotalSafe(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(1) : '—';
}

function renderConferences() {
  return `
    <div class="page-title">Conferences</div>
    <div class="page-sub">All conference pages and simulations below use the updated team assignments from columns L:M on the schedule sheet.</div>
    <div class="grid cols-2" style="margin-top:16px">
      ${DB.conferences.map(c=>`<div class="card" style="cursor:pointer" onclick="location.hash='#conference/${c.slug}'; route();">
        <div class="section-title"><span class="linkish">${c.conference}</span></div>
        <div class="small">${c.num_teams} teams · avg strength ${c.average_strength.toFixed(1)}</div>
        <div class="small" style="margin-top:8px">Favorite: ${linkTeam(c.teams[0].team)} (${fmtPct(c.teams[0].conference_title_pct)})</div>
        <div class="small" style="margin-top:8px">Next: ${linkTeam(c.teams[1].team)} (${fmtPct(c.teams[1].conference_title_pct)})</div>
        <div class="small" style="margin-top:10px"><span class="linkish">Open conference page →</span></div>
      </div>`).join('')}
    </div>
  `;
}
function renderConference(slug) {
  const c = confBySlug[slug];
  if (!c) return `<div class="page-title">Conference not found</div>`;
  const confGames = DB.games.filter(g => g.is_conference_game && g.home_conference===c.conference && g.away_conference===c.conference);
  return `
    <div class="page-title">${c.conference}</div>
    <div class="page-sub">${c.num_teams} teams · conference mapping refreshed from columns L:M</div>
    <div class="grid cols-3" style="margin-top:16px">
      <div class="card"><div class="kpi">Favorite</div><div class="kpi-value">${teamLabel(c.teams[0].team)}</div><div class="kpi-sub">${fmtPct(c.teams[0].conference_title_pct)} conference title</div></div>
      <div class="card"><div class="kpi">Average Strength</div><div class="kpi-value">${c.average_strength.toFixed(1)}</div><div class="kpi-sub">Mean Power Rating</div></div>
      <div class="card"><div class="kpi">Conference Games</div><div class="kpi-value">${confGames.length}</div><div class="kpi-sub">Used in current simulation</div></div>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="section-title">Projected Standings / Title Odds</div>
      <table><thead><tr><th>Team</th><th>Rank</th><th>Power Rating</th><th>Avg Wins</th><th>Avg Conf Wins</th><th>Conf SOS Adj</th><th>Title %</th><th>Title Odds</th></tr></thead><tbody>
      ${c.teams.map(t=>`<tr><td>${linkTeam(t.team)}</td><td>${t.rank}</td><td>${t.combo.toFixed(1)}</td><td>${t.avg_total_wins.toFixed(2)}</td><td>${t.avg_conference_wins.toFixed(2)}</td><td>${fmtSOS(confSOSByTeam[t.team])} (#${confSOSRankByTeam[t.team] ?? '—'})</td><td>${fmtPct(t.conference_title_pct)}</td><td>${americanOddsFromProb(t.conference_title_pct)}</td></tr>`).join('')}
      </tbody></table>
    </div>
    ${renderConferenceMarketTable(c.conference, c.teams)}
    <div style="margin-top:16px">${scheduleTable(confGames)}</div>
  `;
}
function renderSimulations() {
  const topTitles = DB.conferences.map(c=>({conf:c.conference, team:c.teams[0].team, pct:c.teams[0].conference_title_pct}));
  const topMake = DB.conferences.map(c=>{
    const t = [...c.teams].sort((a,b)=>b.make_title_game_pct-a.make_title_game_pct)[0];
    return {conf:c.conference, team:t.team, pct:t.make_title_game_pct};
  });
  const mostUncertain = [...DB.teams].sort((a,b)=>Math.abs(0.5-a.bowl_eligibility_pct)-Math.abs(0.5-b.bowl_eligibility_pct)).slice(0,12);
  return `
    <div class="page-title">Simulations</div>
    <div class="page-sub">Conference title-game templates/site types come from Week 14. Tiebreakers use head-to-head, common opponents, record vs highest-placed common opponent, then Power Rating.</div>
    <div class="grid cols-2" style="margin-top:16px">
      <div class="card">
        <div class="section-title">Conference Favorites</div>
        <table><thead><tr><th>Conference</th><th>Favorite</th><th>Win Conf %</th></tr></thead><tbody>
        ${topTitles.map(r=>`<tr><td>${linkConf(r.conf)}</td><td>${linkTeam(r.team)}</td><td>${fmtPct(r.pct)}</td></tr>`).join('')}
        </tbody></table>
      </div>
      <div class="card">
        <div class="section-title">Most Likely to Make Title Game</div>
        <table><thead><tr><th>Conference</th><th>Team</th><th>Make Title Gm %</th></tr></thead><tbody>
        ${topMake.map(r=>`<tr><td>${linkConf(r.conf)}</td><td>${linkTeam(r.team)}</td><td>${fmtPct(r.pct)}</td></tr>`).join('')}
        </tbody></table>
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="section-title">Conference Championship Games</div>
      <table><thead><tr><th>Conference</th><th>Template</th><th>Site Type</th><th>Projected Matchup</th><th>Spread</th><th>Total</th><th>Favorite</th></tr></thead><tbody>
      ${DB.conferences.map(c=>{
        const cg = c.championship_game;
        if (!cg) return '';
        const fav = cg.projected_spread >= 0 ? cg.projected_matchup.home_team : cg.projected_matchup.away_team;
        const spread = `${fav} -${Math.abs(cg.projected_spread).toFixed(1)}`;
        return `<tr><td>${linkConf(c.conference)}</td><td>${cg.template}</td><td>${cg.site_type}</td><td>${linkTeam(cg.projected_matchup.away_team)} at ${linkTeam(cg.projected_matchup.home_team)}</td><td>${spread}</td><td>${cfmtProjectedTotalSafe(g.projected_total)}</td><td>${linkTeam(fav)}</td></tr>`;
      }).join('')}
      </tbody></table>
    </div>
    <div class="grid cols-2" style="margin-top:16px">
      <div class="card">
        <div class="section-title">Make Title Game Leaders</div>
        <table><thead><tr><th>Team</th><th>Conf</th><th>Make Title Gm %</th><th>Win Conf %</th></tr></thead><tbody>
        ${[...DB.teams].sort((a,b)=>b.make_title_game_pct-a.make_title_game_pct).slice(0,15).map(t=>`<tr><td>${linkTeam(t.team)}</td><td>${linkConf(t.conference)}</td><td>${fmtPct(t.make_title_game_pct)}</td><td>${fmtPct(t.conference_title_pct)}</td></tr>`).join('')}
        </tbody></table>
      </div>
      <div class="card">
        <div class="section-title">Most Uncertain Bowl Cases</div>
        <table><thead><tr><th>Team</th><th>Conf</th><th>Avg Wins</th><th>Bowl %</th></tr></thead><tbody>
        ${mostUncertain.map(t=>`<tr><td>${linkTeam(t.team)}</td><td>${linkConf(t.conference)}</td><td>${t.avg_total_wins.toFixed(2)}</td><td>${fmtPct(t.bowl_eligibility_pct)}</td></tr>`).join('')}
        </tbody></table>
      </div>
    </div>
  `;
}
function setBettingSeason(season) {
  bettingSeason = season;
  if (location.hash === '#betting') {
    byId('app').innerHTML = renderBetting();
    mountBettingFilters();
  }
}

function renderResultsCenter() {
  const summary = getResultsSummary();
  const completed = summary.finals.length;
  const remaining = DB.games.length - completed;
  const teamsWithGames = Object.entries(summary.teamStats)
    .map(([team, s]) => ({team, ...s}))
    .filter(t => t.wins + t.losses > 0)
    .sort((a,b) => (b.wins-b.losses) - (a.wins-a.losses) || b.wins - a.wins)
    .slice(0, 12);
  const weeksAll = [...new Set(DB.games.map(g => g.week))].sort((a,b)=>a-b);
  return `
    <div class="hero">
      <div>
        <div class="page-title">Season Results Update Center</div>
        <div class="page-sub">CFBD-ready control room for game status and scores. Embedded CFBD game IDs/status flow in automatically; final scores will appear after completed CFBD pulls; manual browser overrides remain as a fallback.</div>
      </div>
      <div class="hero-stats">
        <div class="mini"><div class="label">Completed Games</div><div class="value">${completed}</div></div>
        <div class="mini"><div class="label">Remaining Games</div><div class="value">${remaining}</div></div>
        <div class="mini"><div class="label">Weeks Loaded</div><div class="value">${weeksAll.length}</div></div>
      </div>
    </div>
    <div class="grid cols-2" style="margin-top:16px">
      <div class="card">
        <div class="section-title">How this prototype works</div>
        <div class="small">When CFBD final scores are embedded in the site data, games appear as <b>Final · CFBD</b> automatically. Use manual entry only for corrections or games not yet matched by the feed.</div>
        <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
          <button class="pill" id="exportResultsBtn">Export results JSON</button>
          <button class="pill" id="importResultsBtn">Import results JSON</button>
          <button class="pill" id="clearResultsBtn">Clear all saved results</button>
        </div>
        <div style="margin-top:12px"><textarea id="resultsJsonBox" class="json-box" placeholder="Exported/imported results JSON will appear here"></textarea></div>
      </div>
      <div class="card">
        <div class="section-title">Actual Records So Far</div>
        <table><thead><tr><th>Team</th><th>Record</th><th>Conf</th><th>Pts For</th><th>Pts Ag</th></tr></thead><tbody>
        ${teamsWithGames.length ? teamsWithGames.map(t=>`<tr><td>${linkTeam(t.team)}</td><td>${t.wins}-${t.losses}</td><td>${t.conf_wins}-${t.conf_losses}</td><td>${t.pf}</td><td>${t.pa}</td></tr>`).join('') : `<tr><td colspan="5" class="muted">No final games entered yet.</td></tr>`}
        </tbody></table>
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="section-title">Game Results and Overrides</div>
      <div class="filters">
        <select id="resultsWeek"><option value="all">All weeks</option>${weeksAll.map(w=>`<option value="${w}">Week ${w}</option>`).join('')}</select>
        <select id="resultsConf"><option value="all">All conferences</option>${DB.conferences.map(c=>`<option value="${c.conference}">${c.conference}</option>`).join('')}</select>
        <input id="resultsTeam" placeholder="Filter team">
        <select id="resultsStatus"><option value="all">All statuses</option><option value="scheduled">Scheduled</option><option value="final">Final</option></select>
      </div>
      <div id="resultsCenterWrap"></div>
    </div>
  `;
}
function mountResultsCenter() {
  const jsonBox = byId('resultsJsonBox');
  function draw() {
    const week = byId('resultsWeek').value;
    const conf = byId('resultsConf').value;
    const team = byId('resultsTeam').value.trim().toLowerCase();
    const status = byId('resultsStatus').value;
    let games = [...DB.games];
    if (week !== 'all') games = games.filter(g => String(g.week) === String(week));
    if (conf !== 'all') games = games.filter(g => g.home_conference===conf || g.away_conference===conf);
    if (team) games = games.filter(g => g.home_team.toLowerCase().includes(team) || g.away_team.toLowerCase().includes(team));
    if (status !== 'all') games = games.filter(g => gameState(g).status === status);

    byId('resultsCenterWrap').innerHTML = `<table>
      <thead><tr><th>Week</th><th>Date</th><th>Away</th><th>Home</th><th>Source</th><th>Status</th><th>Away Score</th><th>Home Score</th><th>Result</th><th>CFBD ID</th><th>Actions</th></tr></thead>
      <tbody>
      ${games.map(g => {
        const st = gameState(g);
        return `<tr>
          <td>${g.week}</td>
          <td>${fmtDate(g.date)}</td>
          <td>${linkTeam(g.away_team)}</td>
          <td>${linkTeam(g.home_team)}</td>
          <td>${st.source === 'manual' ? '<span class="data-chip manual">Manual</span>' : st.source === 'CFBD' ? '<span class="data-chip final">CFBD</span>' : '<span class="data-chip missing">Schedule</span>'}</td>
          <td>
            <select id="status_${g.game_id}">
              <option value="scheduled" ${st.status==='scheduled'?'selected':''}>Scheduled</option>
              <option value="final" ${st.status==='final'?'selected':''}>Final</option>
            </select>
          </td>
          <td><input class="score-input" id="away_${g.game_id}" type="number" min="0" step="1" value="${st.away_score ?? ''}"></td>
          <td><input class="score-input" id="home_${g.game_id}" type="number" min="0" step="1" value="${st.home_score ?? ''}"></td>
          <td>${(() => { const r = gameResultParts(g); return r.winner === '—' ? '—' : `${linkTeam(r.winner)} by ${Math.abs(Number(r.margin))}`; })()}</td>
          <td>${st.cfbd_game_id || g.cfbd_game_id || '—'}</td>
          <td style="white-space:nowrap">
            <button class="icon-btn" onclick="saveGameResult('${g.game_id}')">Save</button>
            <button class="icon-btn" onclick="resetGameResult('${g.game_id}')">Reset</button>
          </td>
        </tr>`;
      }).join('')}
      </tbody></table>`;
  }
  window.saveGameResult = function(gameId) {
    const status = byId(`status_${gameId}`).value;
    const away = byId(`away_${gameId}`).value;
    const home = byId(`home_${gameId}`).value;
    setGameState(gameId, {status, away_score: away, home_score: home});
    draw();
  };
  window.resetGameResult = function(gameId) {
    clearGameState(gameId);
    draw();
  };
  ['resultsWeek','resultsConf','resultsTeam','resultsStatus'].forEach(id => byId(id).addEventListener('input', draw));
  byId('exportResultsBtn').addEventListener('click', () => { jsonBox.value = exportResultsJson(); });
  byId('importResultsBtn').addEventListener('click', () => {
    try {
      importResultsJson(jsonBox.value);
      draw();
      alert('Results imported.');
    } catch (e) {
      alert('Import failed: ' + e.message);
    }
  });
  byId('clearResultsBtn').addEventListener('click', () => {
    if (!confirm('Clear all saved result overrides?')) return;
    resultsState = {};
    saveResultsState();
    jsonBox.value = '';
    draw();
  });
  draw();
}

function buildNav() {
  byId('nav').innerHTML = [
    navBtn('#/','Home'),
    navBtn('#schedule','Season Schedule'),
    navBtn('#results-center','Results Center'),
    navBtn('#rankings','Rankings'),
    navBtn('#market-edges','Futures Market'),
    navBtn('#simulations','Simulations'),
    navBtn('#conferences','Conferences'),
    navBtn('#coach-betting','Coach Trends'),
    navBtn('#betting','Betting')
  ].join('');
}
function route() {
  buildNav();
  const hash = location.hash || '#/';
  let html = '';
  if (hash==='#/' || hash==='#' || hash==='#home') html = renderHome();
  else if (hash==='#schedule') html = renderSchedule();
  else if (hash==='#results-center') html = renderResultsCenter();
  else if (hash==='#rankings') html = renderRankings();
  else if (hash==='#market-edges') html = renderMarketBoard();
  else if (hash==='#simulations') html = renderSimulations();
  else if (hash==='#conferences') html = renderConferences();
  else if (hash==='#coach-betting') html = renderCoachBetting();
  else if (hash==='#betting') html = renderBetting();
  else if (hash.startsWith('#team/')) html = renderTeam(hash.split('/')[1]);
  else if (hash.startsWith('#conference/')) html = renderConference(hash.split('/')[1]);
  else html = '<div class="page-title">Page not found</div>';
  byId('app').innerHTML = html;
  if (hash==='#schedule') mountScheduleFilters();
  if (hash==='#results-center') mountResultsCenter();
  if (hash==='#rankings') mountRankSortControls();
  if (hash==='#market-edges') mountMarketBoardControls();
  if (hash==='#coach-betting') mountCoachBettingControls();
  if (hash==='#betting') mountBettingFilters();
}
function goToTeam() {
  const val = byId('teamSearch').value.trim().toLowerCase();
  if (!val) return;
  const exact = teamByName[val];
  if (exact) { location.hash = '#team/' + exact.slug; return; }
  const partial = DB.teams.find(t => t.team.toLowerCase().includes(val));
  if (partial) location.hash = '#team/' + partial.slug;
  else alert('Team not found');
}
byId('searchBtn').addEventListener('click', goToTeam);
byId('teamSearch').addEventListener('keydown', e => { if (e.key==='Enter') goToTeam(); });
byId('teamList').innerHTML = DB.teams.map(t=>`<option value="${t.team}"></option>`).join('');
window.addEventListener('hashchange', route);
route();



(function removeOUIndividualNoMoveBadges(){
  function clean(){
    document.querySelectorAll('.market-open-current').forEach(el => {
      const txt = (el.textContent || '').trim().toLowerCase();
      if (txt === 'o no move' || txt === 'u no move') {
        el.remove();
      }
    });
  }
  clean();

  const obs = new MutationObserver(clean);
  obs.observe(document.body, { childList: true, subtree: true });
})();



(function removeOUIndividualNoMoveBadges(){
  function clean(){
    const targets = ['o no move', 'u no move'];

    document.querySelectorAll('span, div, em, small').forEach(el => {
      const txt = (el.textContent || '').replace(/\s+/g, ' ').trim().toLowerCase();

      if (targets.includes(txt)) {
        el.remove();
        return;
      }

      // Also remove wrappers that only contain one of those phrases.
      if (
        el.children.length === 1 &&
        targets.includes((el.innerText || '').replace(/\s+/g, ' ').trim().toLowerCase())
      ) {
        el.remove();
      }
    });
  }

  clean();
  setTimeout(clean, 100);
  setTimeout(clean, 500);
  setTimeout(clean, 1000);
  setTimeout(clean, 2000);

  const obs = new MutationObserver(clean);
  obs.observe(document.documentElement, { childList: true, subtree: true, characterData: true });
})();



(function marketMovesTabPatch(){
  function escapeHtmlLocal(v){
    return String(v == null ? '' : v)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }
  function linkTeamLocal(team){
    try { if (typeof linkTeam === 'function') return linkTeam(team); } catch(e) {}
    return '<span class="market-move-team">' + escapeHtmlLocal(team) + '</span>';
  }
  function parseMoveDate(v){
    if (!v) return null;
    const d = new Date(String(v).slice(0, 10) + 'T00:00:00Z');
    return Number.isNaN(d.getTime()) ? null : d;
  }
  function fmtMoveDate(v){
    const d = parseMoveDate(v);
    if (!d) return escapeHtmlLocal(v || '—');
    return d.toISOString().slice(0, 10);
  }
  function impliedProbFromAmerican(v){
    const n = Number(v);
    if (!Number.isFinite(n) || n === 0) return null;
    return n > 0 ? 100 / (n + 100) : Math.abs(n) / (Math.abs(n) + 100);
  }
  function impliedDeltaPct(prev, latest){
    const a = impliedProbFromAmerican(prev);
    const b = impliedProbFromAmerican(latest);
    if (a == null || b == null) return '';
    return ((b - a) * 100).toFixed(2).replace(/\.00$/, '');
  }
  function fmtOdds(v){
    const n = Number(v);
    if (!Number.isFinite(n)) return v == null ? '' : String(v);
    return n > 0 ? `+${n}` : String(n);
  }
  function maxDateFromRows(rows, fields){
    const times = [];
    (rows || []).forEach(r => fields.forEach(f => {
      const d = parseMoveDate(r && r[f]);
      if (d) times.push(d.getTime());
    }));
    return times.length ? new Date(Math.max(...times)).toISOString().slice(0, 10) : '';
  }
  function synthesizeMovesFromCurrentMovement(){
    const out = [];
    (DB.market_win_totals_movement || []).forEach(r => {
      const date = r.latest_snapshot_date || '';
      if (Number(r.win_total_move || 0) !== 0) {
        out.push({market:'Win Total', snapshot_prev:r.first_snapshot_date, snapshot_latest:date, season:r.season, conference:r.conference || '', team:r.team, book:r.book, field:'Win Total', previous:String(r.opening_win_total), latest:String(r.current_win_total), change:String(r.win_total_move), implied_prob_change_pct:'', bet_label:'Win total moved', summary:`${r.team} ${r.book} win total ${r.opening_win_total} → ${r.current_win_total}`});
      }
      if (Number(r.over_odds_move || 0) !== 0) {
        out.push({market:'Win Total', snapshot_prev:r.first_snapshot_date, snapshot_latest:date, season:r.season, conference:r.conference || '', team:r.team, book:r.book, field:'Over Odds', previous:fmtOdds(r.opening_over_odds), latest:fmtOdds(r.current_over_odds), change:String(r.over_odds_move), implied_prob_change_pct:impliedDeltaPct(r.opening_over_odds, r.current_over_odds), win_total_latest:String(r.current_win_total ?? ''), bet_label:`Over ${r.current_win_total} wins`, summary:`${r.team} ${r.book} over ${fmtOdds(r.opening_over_odds)} → ${fmtOdds(r.current_over_odds)}`});
      }
      if (Number(r.under_odds_move || 0) !== 0) {
        out.push({market:'Win Total', snapshot_prev:r.first_snapshot_date, snapshot_latest:date, season:r.season, conference:r.conference || '', team:r.team, book:r.book, field:'Under Odds', previous:fmtOdds(r.opening_under_odds), latest:fmtOdds(r.current_under_odds), change:String(r.under_odds_move), implied_prob_change_pct:impliedDeltaPct(r.opening_under_odds, r.current_under_odds), win_total_latest:String(r.current_win_total ?? ''), bet_label:`Under ${r.current_win_total} wins`, summary:`${r.team} ${r.book} under ${fmtOdds(r.opening_under_odds)} → ${fmtOdds(r.current_under_odds)}`});
      }
    });
    (DB.market_conference_futures_movement || []).forEach(r => {
      if (Number(r.american_odds_move || 0) === 0 && Number(r.implied_prob_move || 0) === 0) return;
      out.push({market:'Conference Title', snapshot_prev:r.first_snapshot_date, snapshot_latest:r.latest_snapshot_date || '', season:r.season, conference:r.conference || '', team:r.team, book:r.book, field:'American Odds', previous:fmtOdds(r.opening_american_odds), latest:fmtOdds(r.current_american_odds), change:String(r.american_odds_move || ''), implied_prob_change_pct:(Number(r.implied_prob_move || 0) * 100).toFixed(2).replace(/\.00$/, ''), bet_label:`${r.conference || 'Conference'} title odds`, summary:`${r.team} ${r.book} ${r.conference || ''} title ${fmtOdds(r.opening_american_odds)} → ${fmtOdds(r.current_american_odds)}`});
    });
    return out;
  }
  function getEmbeddedDailyMoves(){
    const el = document.getElementById('daily-market-moves-data');
    if (!el) return [];
    try { return JSON.parse(el.textContent || '[]'); } catch(e) { return []; }
  }
  function getAllMoves(){
    const embedded = getEmbeddedDailyMoves();
    const embeddedMax = maxDateFromRows(embedded, ['snapshot_latest','move_date','date']);
    const currentMax = maxDateFromRows([...(DB.market_win_totals_raw || []), ...(DB.market_conference_futures_raw || []), ...(DB.market_win_totals_movement || []), ...(DB.market_conference_futures_movement || [])], ['snapshot_date','latest_snapshot_date']);
    // The 8am build can carry stale daily-market-move rows even when the raw market board is current.
    // If that happens, synthesize the moves panel from the current open-to-latest movement tables.
    if (currentMax && (!embeddedMax || embeddedMax < currentMax)) return synthesizeMovesFromCurrentMovement();
    return embedded;
  }
  function getMoves(){
    const all = getAllMoves();
    const dated = all.map(m => ({ move: m, date: parseMoveDate(m.snapshot_latest || m.move_date || m.date) })).filter(x => x.date);
    if (!dated.length) return all;
    const maxTime = Math.max(...dated.map(x => x.date.getTime()));
    const cutoff = maxTime - 6 * 24 * 60 * 60 * 1000;
    return dated.filter(x => x.date.getTime() >= cutoff).map(x => x.move);
  }
  function dateRangeLabel(moves){
    const dates = moves.map(m => parseMoveDate(m.snapshot_latest || m.move_date || m.date)).filter(Boolean).map(d => d.getTime());
    if (!dates.length) return '';
    const min = new Date(Math.min(...dates)).toISOString().slice(0, 10);
    const max = new Date(Math.max(...dates)).toISOString().slice(0, 10);
    return min === max ? min : `${min} to ${max}`;
  }
  function pullLabel(moves){
    if (!moves.length) return 'No line movement detected in the last 7 days of available pulls';
    const label = dateRangeLabel(moves);
    return label ? `Last 7 days of current movement data · ${label}` : 'Last 7 days of current movement data';
  }
  function moveMagnitude(m){
    const n = Number(m.implied_prob_change_pct);
    if (!Number.isNaN(n) && Number.isFinite(n)) return Math.abs(n);
    const c = Number(m.change);
    return Number.isFinite(c) ? Math.abs(c) : 0;
  }
  const MARKET_MOVES_SORT_DEFAULT = { key: 'date', dir: 'desc' };
  function currentMovesSort(){
    try {
      const saved = JSON.parse(localStorage.getItem('ncaaf_market_moves_sort') || 'null');
      if (saved && saved.key) return { key: saved.key, dir: saved.dir === 'asc' ? 'asc' : 'desc' };
    } catch(e) {}
    return Object.assign({}, MARKET_MOVES_SORT_DEFAULT);
  }
  function setCurrentMovesSort(key){
    const cur = currentMovesSort();
    const next = { key, dir: (cur.key === key && cur.dir === 'desc') ? 'asc' : 'desc' };
    localStorage.setItem('ncaaf_market_moves_sort', JSON.stringify(next));
    return next;
  }
  function moveSortValue(m, key){
    if (key === 'date') {
      const d = parseMoveDate(m.snapshot_latest || m.move_date || m.date);
      return d ? d.getTime() : 0;
    }
    if (key === 'market') return String(m.market || '').toLowerCase();
    if (key === 'team') return String(m.team || '').toLowerCase();
    if (key === 'book') return String(m.book || '').toLowerCase();
    if (key === 'bet') return String(m.bet_label || m.field || '').toLowerCase();
    if (key === 'move') return moveMagnitude(m);
    return '';
  }
  function sortMovesList(moves){
    const sort = currentMovesSort();
    const dir = sort.dir === 'asc' ? 1 : -1;
    return moves.slice().sort((a,b)=>{
      const av = moveSortValue(a, sort.key);
      const bv = moveSortValue(b, sort.key);
      let cmp = 0;
      if (typeof av === 'number' && typeof bv === 'number') cmp = av - bv;
      else cmp = String(av).localeCompare(String(bv));
      if (cmp !== 0) return cmp * dir;
      // Stable, useful secondary sort: newest first, then biggest move.
      const bd = parseMoveDate(b.snapshot_latest || b.move_date || b.date);
      const ad = parseMoveDate(a.snapshot_latest || a.move_date || a.date);
      const bt = bd ? bd.getTime() : 0;
      const at = ad ? ad.getTime() : 0;
      if (bt !== at) return bt - at;
      return moveMagnitude(b) - moveMagnitude(a);
    });
  }
  function marketMoveHeader(){
    const sort = currentMovesSort();
    const cols = [
      ['date','Date'], ['market','Market'], ['team','Team'],
      ['book','Book'], ['bet','Bet'], ['move','Move']
    ];
    return `<div class="market-move-header">${cols.map(([key,label]) => {
      const arrow = sort.key === key ? (sort.dir === 'asc' ? '▲' : '▼') : '';
      return `<button type="button" data-market-move-sort="${key}">${label}<span class="market-move-sort-arrow">${arrow}</span></button>`;
    }).join('')}</div>`;
  }
  function readMarketMovesRows(){
  const el = document.getElementById('daily-market-moves-data');
  if (!el) return [];
  try { return JSON.parse(el.textContent || '[]'); }
  catch(e){ return []; }
}

function marketMoveDisplayDate(row){
  return row.move_date || row.snapshot_latest || '';
}

function marketMoveImpactClass(v){
  const n = Number(v);
  if (!Number.isFinite(n)) return '';
  return n > 0 ? 'imp-pos' : n < 0 ? 'imp-neg' : '';
}

function marketMoveRange(rows){
  const dates = rows.map(marketMoveDisplayDate).filter(Boolean).sort();
  if (!dates.length) return '';
  const first = dates[0];
  const last = dates[dates.length - 1];
  return first === last ? first : `${first} to ${last}`;
}

function sortMarketMoveRows(rows){
  return [...rows].sort((a,b) => {
    const da = String(marketMoveDisplayDate(a));
    const db = String(marketMoveDisplayDate(b));
    if (da !== db) return db.localeCompare(da);
    const ia = Math.abs(Number(a.implied_prob_change_pct || 0));
    const ib = Math.abs(Number(b.implied_prob_change_pct || 0));
    return ib - ia;
  });
}

function renderMovesPanel(){
  const injectedRows = injectedDailyMarketMovesRows();
  const allRows = injectedRows.length ? injectedRows : readMarketMovesRows();
  const rows = sortMarketMoveRows(allRows);
  const winRows = rows.filter(r => String(r.market || '').toLowerCase().includes('win'));
  const confRows = rows.filter(r => String(r.market || '').toLowerCase().includes('conference'));
  const range = marketMoveRange(rows);

  const body = rows.map(r => {
    const imp = r.implied_prob_change_pct;
    const impNum = Number(imp);
    const impText = (imp !== '' && imp != null && Number.isFinite(impNum))
      ? ` <span class="${marketMoveImpactClass(imp)}">${impNum > 0 ? '+' : ''}${impNum}% implied</span>`
      : '';
    const prev = r.previous == null ? '' : String(r.previous);
    const latest = r.latest == null ? '' : String(r.latest);
    return `
      <div class="market-move-row">
        <div class="market-move-date">${escapeHtml(marketMoveDisplayDate(r))}</div>
        <div class="market-move-kind">${escapeHtml(String(r.market || ''))}</div>
        <div class="market-move-team">${typeof linkTeam === 'function' ? linkTeam(r.team) : escapeHtml(String(r.team || ''))}</div>
        <div class="market-move-book">${escapeHtml(String(r.book || ''))}</div>
        <div class="market-move-bet">${escapeHtml(String(r.field || ''))}</div>
        <div class="market-move-change">${escapeHtml(prev)} → ${escapeHtml(latest)}${impText}</div>
      </div>`;
  }).join('');

  return `<div class="market-moves-panel active">
    <div class="market-moves-sticky">
      <div class="market-moves-head">
        <div>
          <div class="market-moves-head-title">Latest Market Moves</div>
          <div class="market-moves-head-sub">Last 7 days of current movement data${range ? ` · ${escapeHtml(range)}` : ''}</div>
        </div>
        <div class="market-moves-pill-row">
          <span class="market-moves-pill">7-day moves: <b>${rows.length}</b></span>
          <span class="market-moves-pill">Win totals: <b>${winRows.length}</b></span>
          <span class="market-moves-pill">Conf futures: <b>${confRows.length}</b></span>
          <span class="market-moves-pill">Loaded rows: <b>${allRows.length}</b></span>
        </div>
      </div>
      <div class="market-move-header">
        <button>Date</button>
        <button>Market</button>
        <button>Team</button>
        <button>Book</button>
        <button>Bet</button>
        <button>Move</button>
      </div>
    </div>
    ${rows.length ? `<div class="market-moves-list">${body}</div>` : `<div class="market-move-empty">No recent market moves loaded.</div>`}
  </div>`;
}
  /* MARKET_MOVES_IIFE_CLOSE_FIX */
})();



(function openingPossessionSiteFeature(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function rows(){
    if (typeof DB === 'undefined') return [];
    return DB.coach_opening_possession_tendency_2026
      || DB.coach_coin_toss_current_2026
      || DB.coach_coin_toss_decision_current_2026_clean
      || [];
  }

  function lower(s){
    return clean(s).toLowerCase();
  }

  function pct(x){
    const n = Number(x);
    return Number.isFinite(n) ? `${n.toFixed(1)}%` : '—';
  }

  function num(x){
    const n = Number(x);
    return Number.isFinite(n) ? n : 0;
  }

  function findByTeam(team){
    const key = lower(team);
    return rows().find(r => lower(r.team) === key) || null;
  }

  function findByCoach(coach, team){
    const coachKey = lower(coach);
    const teamKey = lower(team);
    let hit = rows().find(r => lower(r.head_coach) === coachKey && (!teamKey || lower(r.team) === teamKey));
    if (!hit) hit = rows().find(r => lower(r.head_coach) === coachKey);
    return hit || null;
  }

  function receiveProb(my, opp){
    if (!my || !opp) return null;
    const a = Number(my.receive_pct);
    const b = Number(opp.defer_pct);
    if (!Number.isFinite(a) || !Number.isFinite(b)) return null;
    return Math.round(((a + b) / 2) * 10) / 10;
  }

  function edgeMarks(diff){
    const d = Math.abs(diff);
    if (d >= 25) return '✓✓✓';
    if (d >= 15) return '✓✓';
    if (d >= 8) return '✓';
    return '';
  }

  function edgeBadge(team, marks){
    if (!marks) return '<span class="cfb-edge-pill even">—</span>';
    if (typeof cfbEdgeBadge === 'function') return cfbEdgeBadge(team, marks.length, 'away');
    return `<span class="cfb-edge-pill edge-away">${team} ${marks}</span>`;
  }

  function dash(){
    return '<span class="cfb-edge-pill even">—</span>';
  }

  function teamValueHtml(row, prob){
    if (!row) {
      return `<span class="open-pos-context-main">No sample</span>`;
    }
    const tendency = clean(row.opening_possession_tendency || 'Mixed');
    const tossWins = num(row.toss_wins);
    const recv = num(row.receive_take_ball);
    const defer = num(row.defer);
    return `<span class="open-pos-context-main">${tendency}</span>
      <span class="open-pos-context-sub">Won toss ${tossWins}x · receive ${recv}/${tossWins} (${pct(row.receive_pct)}) · defer ${defer}/${tossWins} (${pct(row.defer_pct)})</span>
      <span class="open-pos-context-sub">Projected receive opening kick: ${prob == null ? '—' : pct(prob)}</span>`;
  }

  function addMatchupRows(){
    document.querySelectorAll('.cfb-context-table').forEach(table => {
      if (table.dataset.openingPossessionAdded === '1') return;

      const theadCells = Array.from(table.querySelectorAll('thead th')).map(th => clean(th.textContent));
      const tbody = table.querySelector('tbody');
      if (!tbody || theadCells.length < 4) return;

      let split = false;
      let away = '';
      let home = '';

      // Split layout: Away Edge | Away | Metric | Home | Home Edge
      if (theadCells.length >= 5 && /metric/i.test(theadCells[2])) {
        split = true;
        away = clean(theadCells[1]);
        home = clean(theadCells[3]);
      } else {
        // Old layout: Category | Away | Home | Edge
        away = clean(theadCells[1]);
        home = clean(theadCells[2]);
      }

      if (!away || !home || away.toLowerCase().includes('edge') || home.toLowerCase().includes('edge')) return;

      const a = findByTeam(away);
      const h = findByTeam(home);
      const aProb = receiveProb(a, h);
      const hProb = receiveProb(h, a);

      let aEdge = dash();
      let hEdge = dash();
      let singleEdge = dash();

      if (aProb != null && hProb != null) {
        const diff = aProb - hProb;
        const marks = edgeMarks(diff);
        if (marks && diff > 0) {
          aEdge = edgeBadge(away, marks);
          singleEdge = aEdge;
        } else if (marks && diff < 0) {
          hEdge = edgeBadge(home, marks);
          singleEdge = hEdge;
        }
      }

      let html = '';
      if (split) {
        html = `<tr>
          <td class="cfb-edge-cell cfb-context-away-edge">${aEdge}</td>
          <td class="cfb-context-team-val">${teamValueHtml(a, aProb)}</td>
          <td class="cfb-context-cat">Opening Possession</td>
          <td class="cfb-context-team-val">${teamValueHtml(h, hProb)}</td>
          <td class="cfb-edge-cell cfb-context-home-edge">${hEdge}</td>
        </tr>`;
      } else {
        html = `<tr>
          <td>Opening Possession</td>
          <td>${teamValueHtml(a, aProb)}</td>
          <td>${teamValueHtml(h, hProb)}</td>
          <td>${singleEdge}</td>
        </tr>`;
      }

      tbody.insertAdjacentHTML('afterbegin', html);
      table.dataset.openingPossessionAdded = '1';
    });
  }

  function findCoachName(card){
    const trs = Array.from(card.querySelectorAll('tr'));
    for (const tr of trs) {
      const cells = Array.from(tr.children);
      if (cells.length >= 2 && /^head coach$/i.test(clean(cells[0].textContent))) {
        return clean(cells[1].textContent);
      }
    }
    const txt = clean(card.textContent);
    const m = txt.match(/Head Coach\s+(.+?)\s+Tracked Teams/i);
    return m ? clean(m[1]) : '';
  }

  function findDashboardTeam(){
    const title = clean(document.querySelector('.page-title')?.textContent || '');
    if (title) return title.replace(/\s+Team Dashboard$/i,'').trim();
    return '';
  }

  function renderDashboardBox(row){
    if (!row) {
      return `<div class="coach-toss-dashboard-box">
        <div class="coach-toss-dashboard-title">Coin Toss / Opening Possession</div>
        <div class="coach-toss-note">No explicit ESPN toss-decision sample found for this current coach.</div>
      </div>`;
    }

    const tossWins = num(row.toss_wins);
    const receive = num(row.receive_take_ball);
    const defer = num(row.defer);
    const tendency = clean(row.opening_possession_tendency || 'Mixed');
    const confidence = clean(row.confidence || '');
    const teams = clean(row.teams_in_sample || '');
    const seasons = clean(row.seasons || '');

    const tendencyClass = tendency.toLowerCase().includes('take-ball') ? 'good'
      : tendency.toLowerCase().includes('defer') ? 'warn'
      : '';

    return `<div class="coach-toss-dashboard-box">
      <div class="coach-toss-dashboard-title">
        <div>Coin Toss / Opening Possession</div>
        <span>${confidence ? `Confidence: ${confidence}` : 'Explicit ESPN sample'}</span>
      </div>
      <div class="coach-toss-grid">
        <div class="coach-toss-kpi">
          <div class="label">Tendency</div>
          <div class="value ${tendencyClass}">${tendency}</div>
        </div>
        <div class="coach-toss-kpi">
          <div class="label">Take ball</div>
          <div class="value">${receive}/${tossWins} · ${pct(row.receive_pct)}</div>
        </div>
        <div class="coach-toss-kpi">
          <div class="label">Defer</div>
          <div class="value">${defer}/${tossWins} · ${pct(row.defer_pct)}</div>
        </div>
      </div>
      <div class="coach-toss-note">
        Won toss sample: <b>${tossWins}</b>${seasons ? ` · Seasons: ${seasons}` : ''}${teams ? ` · Sample teams: ${teams}` : ''}. 
        Source: explicit ESPN toss rows matched to exact team-season head coach.
      </div>
    </div>`;
  }

  function addDashboardBox(){
    document.querySelectorAll('.card').forEach(card => {
      const text = clean(card.textContent);
      if (!text.includes('Head Coach Betting Trends')) return;
      if (card.querySelector('.coach-toss-dashboard-box')) return;

      const coach = findCoachName(card);
      const team = findDashboardTeam();
      const row = findByCoach(coach, team);

      card.insertAdjacentHTML('beforeend', renderDashboardBox(row));
    });
  }

  function run(){
    if (!rows().length) return;
    addMatchupRows();
    addDashboardBox();
  }

  run();
  setTimeout(run, 100);
  setTimeout(run, 500);
  setTimeout(run, 1200);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1200);
  });

  window.addEventListener('hashchange', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
  });
})();



(function coachSituationalSystemsFeature(){
  function clean(s){ return String(s || '').replace(/\s+/g,' ').trim(); }
  function lower(s){ return clean(s).toLowerCase(); }
  function rows(){
    if (typeof DB === 'undefined') return [];
    return DB.coach_betting_system_current_2026 || [];
  }
  function pct(x){ const n = Number(x); return Number.isFinite(n) ? `${n.toFixed(1)}%` : '—'; }
  function margin(x){ const n = Number(x); return Number.isFinite(n) ? `${n >= 0 ? '+' : ''}${n.toFixed(2)}` : '—'; }
  function gradeClass(g){
    const s = lower(g);
    if (s.includes('fade')) return 'fade';
    if (s.includes('edge')) return 'edge';
    if (s.includes('watch')) return 'watch';
    return '';
  }
  function gradePriority(g){
    const s = lower(g);
    if (s.includes('strong coach edge')) return 1;
    if (s.includes('medium coach edge')) return 2;
    if (s === 'watch') return 3;
    if (s.includes('strong coach fade')) return 4;
    if (s.includes('medium coach fade')) return 5;
    if (s.includes('watch fade')) return 6;
    return 99;
  }
  function findCoachName(card){
    const trs = Array.from(card.querySelectorAll('tr'));
    for (const tr of trs) {
      const cells = Array.from(tr.children);
      if (cells.length >= 2 && /^head coach$/i.test(clean(cells[0].textContent))) return clean(cells[1].textContent);
    }
    const txt = clean(card.textContent);
    const m = txt.match(/Head Coach\s+(.+?)\s+Tracked Teams/i);
    return m ? clean(m[1]) : '';
  }
  function findTeamName(){
    const title = clean(document.querySelector('.page-title')?.textContent || '');
    return title.replace(/\s+Team Dashboard$/i,'').trim();
  }
  function coachRows(coach, team){
    const ck = lower(coach), tk = lower(team);
    let hits = rows().filter(r => lower(r.head_coach) === ck && (!tk || lower(r.team) === tk));
    if (!hits.length) hits = rows().filter(r => lower(r.head_coach) === ck);
    return hits
      .filter(r => clean(r.grade) && clean(r.grade).toLowerCase() !== 'no sample' && Number(r.games || 0) >= 3)
      .sort((a,b) => (gradePriority(a.grade)-gradePriority(b.grade)) || (Number(b.games||0)-Number(a.games||0)) || (Number(b.avg_ats_margin||0)-Number(a.avg_ats_margin||0)))
      .slice(0,5);
  }
  function recordText(r){
    const pushes = Number(r.pushes || 0);
    const rec = `${Number(r.wins||0)}-${Number(r.losses||0)}${pushes ? '-' + pushes : ''}`;
    return `${rec} ATS · ${pct(r.cover_pct)} · ${margin(r.avg_ats_margin)}`;
  }
  function renderBox(items){
    if (!items.length) return `<div class="coach-systems-box"><div class="coach-systems-title"><div>Coach Situational Systems</div><span>Backtest context</span></div><div class="coach-system-note">No qualifying situational coach-system trend found yet.</div></div>`;
    return `<div class="coach-systems-box">
      <div class="coach-systems-title"><div>Coach Situational Systems</div><span>Triggered trends use historical ATS systems</span></div>
      <div class="coach-system-list">
        ${items.map(r => `<div class="coach-system-row">
          <div class="coach-system-name">${clean(r.system_name)}</div>
          <div class="coach-system-record">${recordText(r)}</div>
          <div class="coach-system-grade ${gradeClass(r.grade)}">${clean(r.grade)}</div>
        </div>`).join('')}
      </div>
      <div class="coach-system-note">Coach samples are exact team-season head-coach backtests. Use as context; only matchup-triggered systems should matter on game pages.</div>
    </div>`;
  }
  function run(){
    if (!rows().length) return;
    document.querySelectorAll('.card').forEach(card => {
      const text = clean(card.textContent);
      if (!text.includes('Head Coach Betting Trends')) return;
      if (card.querySelector('.coach-systems-box')) return;
      const coach = findCoachName(card);
      const team = findTeamName();
      card.insertAdjacentHTML('beforeend', renderBox(coachRows(coach, team)));
    });
  }
  run();
  setTimeout(run, 100); setTimeout(run, 500); setTimeout(run, 1200);
  document.addEventListener('click', () => { setTimeout(run,150); setTimeout(run,500); setTimeout(run,1200); });
  window.addEventListener('hashchange', () => { setTimeout(run,150); setTimeout(run,500); });
})();



(function matchupSystemTriggersFeature(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function triggers(){
    if (typeof DB === 'undefined') return [];
    return DB.matchup_system_triggers_2026 || [];
  }

  function norm(s){
    return clean(s).toLowerCase();
  }

  function gradeClass(grade, direction){
    const g = clean(grade).toLowerCase();
    const d = clean(direction).toLowerCase();
    if (g.includes('fade') || d.includes('fade')) return 'warn';
    if (/^a|^b|^c/.test(g)) return 'good';
    return 'neutral';
  }

  function gradeRank(grade){
    const g = clean(grade);
    const order = {
      "A+":1,"A":2,"A-":3,"A Fade":3,
      "B+":4,"B":5,"B-":6,"B Fade":6,
      "C+":7,"C":8,"C-":9,"C Fade":9,
      "D":10,"F":11
    };
    return order[g] || 99;
  }

  function isPrimaryGrade(grade){
    const g = clean(grade);
    return ["A+","A","A-","A Fade","B+","B","B-","B Fade"].includes(g);
  }

  function gameTeamsFromPanel(panel){
    const header = panel.querySelector('.cfb-matchup-header');
    if (header) {
      const names = Array.from(header.querySelectorAll('.cfb-team-name')).map(x => clean(x.textContent));
      if (names.length >= 2) return [names[0], names[1]];
    }

    const heads = Array.from(panel.querySelectorAll('.cfb-side-head')).map(x => clean(x.textContent));
    for (const h of heads) {
      const m = h.match(/^(.+?)\s+OFF\s+VS\s+(.+?)\s+DEF$/i);
      if (m) return [clean(m[1]), clean(m[2])];
    }

    return [];
  }

  function weekFromPanel(panel){
    const txt = clean(panel.textContent);
    const m = txt.match(/\bWeek\s+(\d+)/i);
    return m ? Number(m[1]) : null;
  }

  function candidatesForTeams(teamA, teamB){
    const all = triggers();
    const a = norm(teamA);
    const b = norm(teamB);

    return all.filter(r => {
      const rt = norm(r.team);
      const ro = norm(r.opponent);
      return (rt === a && ro === b) || (rt === b && ro === a);
    });
  }

  function dedupeSystems(list){
    // Keep strongest/specific if duplicates overlap.
    const sorted = list.slice().sort((a,b) => {
      const ga = gradeRank(a.system_grade);
      const gb = gradeRank(b.system_grade);
      if (ga !== gb) return ga - gb;
      return Number(b.games || 0) - Number(a.games || 0);
    });

    const seen = new Set();
    const out = [];

    for (const r of sorted) {
      const key = `${r.team}|${r.system_name}`;
      if (seen.has(key)) continue;

      // Suppress broad "or short rest" if a more specific same-team off-bye system exists.
      const name = clean(r.system_name).toLowerCase();
      if (name.includes('b2b road or short rest')) {
        const hasSpecific = sorted.some(x =>
          norm(x.team) === norm(r.team)
          && clean(x.system_name).toLowerCase() !== name
          && (
            clean(x.system_name).toLowerCase().includes('opponent b2b road')
            || clean(x.system_name).toLowerCase().includes('opponent short rest')
          )
        );
        if (hasSpecific) continue;
      }

      seen.add(key);
      out.push(r);
    }

    return out;
  }

  function itemHtml(r){
    const grade = clean(r.system_grade || r.grade || '');
    const dir = clean(r.direction || '');
    const cls = gradeClass(grade, dir);
    const rec = clean(r.record_text || r.display_text || '');
    const type = clean(r.system_type || '').replace(/_/g,' ');

    return `<div class="system-trigger-item">
      <div class="system-trigger-row">
        <div class="system-trigger-name">${clean(r.system_name)}</div>
        <div class="system-trigger-grade ${cls}">${grade || '—'}</div>
      </div>
      <div class="system-trigger-meta">${dir ? dir + ' · ' : ''}${rec}</div>
      <div class="system-trigger-note">${type}</div>
    </div>`;
  }

  function teamBlock(team, list){
    if (!list.length) {
      return `<div class="system-trigger-team">
        <div class="system-trigger-team-title">${team}</div>
        <div class="system-trigger-empty">
          No A/B-grade betting systems triggered for this team.
          <div class="system-trigger-note">Schedule systems, coach situational systems, and matchup systems are scanned automatically.</div>
        </div>
      </div>`;
    }

    const primary = list.filter(r => isPrimaryGrade(r.system_grade));
    const more = list.filter(r => !isPrimaryGrade(r.system_grade));

    return `<div class="system-trigger-team">
      <div class="system-trigger-team-title">${team}</div>
      <div class="system-trigger-list">
        ${(primary.length ? primary : list.slice(0,3)).map(itemHtml).join('')}
      </div>
      ${more.length && primary.length ? `<details class="system-more-detail">
        <summary>More systems (${more.length})</summary>
        <div class="system-trigger-list" style="margin-top:.45rem">${more.map(itemHtml).join('')}</div>
      </details>` : ''}
    </div>`;
  }

  function renderBox(teamA, teamB, list){
    const cleaned = dedupeSystems(list);
    const aList = cleaned.filter(r => norm(r.team) === norm(teamA));
    const bList = cleaned.filter(r => norm(r.team) === norm(teamB));

    return `<div class="system-trigger-box">
      <div class="system-trigger-title">
        <span>Betting Systems Triggered</span>
        <em>Auto-scanned schedule, matchup, and coach trends</em>
      </div>
      <div class="system-trigger-grid">
        ${teamBlock(teamA, aList)}
        ${teamBlock(teamB, bList)}
      </div>
    </div>`;
  }

  function insertIntoPanel(panel){
    if (!panel || panel.querySelector('.system-trigger-box')) return;

    const teams = gameTeamsFromPanel(panel);
    if (teams.length < 2) return;

    const list = candidatesForTeams(teams[0], teams[1]);
    const html = renderBox(teams[0], teams[1], list);

    const contextTable = panel.querySelector('.cfb-context-table');
    const contextSection = contextTable ? contextTable.closest('.cfb-section') : null;
    if (contextSection) {
      contextSection.insertAdjacentHTML('afterend', html);
    } else {
      panel.insertAdjacentHTML('beforeend', html);
    }
  }

  function run(){
    if (!triggers().length) return;
    document.querySelectorAll('.matchup-panel, .cfb-matchup-shell').forEach(insertIntoPanel);
  }

  run();
  setTimeout(run, 100);
  setTimeout(run, 500);
  setTimeout(run, 1200);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1200);
  });
})();



(function scheduleBettingSystemsColumn(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function normTeam(s){
    return clean(s)
      .replace(/\s*\(#?\d+\)\s*/g,'')
      .replace(/\s+#?\d+\s*$/g,'')
      .toLowerCase();
  }

  function triggers(){
    if (typeof DB === 'undefined') return [];
    return DB.matchup_system_triggers_2026 || [];
  }

  function countFor(team, opponent){
    const t = normTeam(team);
    const o = normTeam(opponent);

    return triggers().filter(r =>
      normTeam(r.team) === t &&
      normTeam(r.opponent) === o
    ).length;
  }

  function teamLine(team, count){
    const cls = count > 0 ? 'schedule-system-count' : 'schedule-system-count zero';
    return `<div class="schedule-system-team">
      <span class="schedule-system-name">${clean(team)}</span>
      <span class="${cls}">${count}</span>
    </div>`;
  }

  function processTable(table){
    if (!table || table.dataset.scheduleSystemsColumn === '1') return;

    const headerRow = table.querySelector('thead tr');
    if (!headerRow) return;

    const headers = Array.from(headerRow.children).map(th => clean(th.textContent).toLowerCase());

    const awayIdx = headers.findIndex(h => h === 'away');
    const homeIdx = headers.findIndex(h => h === 'home');
    const matchupIdx = headers.findIndex(h => h.includes('matchup'));

    if (awayIdx < 0 || homeIdx < 0 || matchupIdx < 0) return;

    // Add header before Matchup.
    const th = document.createElement('th');
    th.textContent = 'Betting Systems';
    headerRow.insertBefore(th, headerRow.children[matchupIdx]);

    table.querySelectorAll('tbody tr').forEach(row => {
      if (row.classList.contains('matchup-detail-row')) return;

      const cells = Array.from(row.children);
      if (cells.length <= Math.max(awayIdx, homeIdx, matchupIdx)) return;

      const away = clean(cells[awayIdx].textContent);
      const home = clean(cells[homeIdx].textContent);

      const awayCount = countFor(away, home);
      const homeCount = countFor(home, away);

      const td = document.createElement('td');
      td.className = 'schedule-system-cell';
      td.innerHTML = teamLine(away, awayCount) + teamLine(home, homeCount);

      row.insertBefore(td, row.children[matchupIdx]);
    });

    table.dataset.scheduleSystemsColumn = '1';
  }

  function run(){
    if (!triggers().length) return;

    document.querySelectorAll('table').forEach(table => {
      const txt = clean(table.querySelector('thead')?.textContent || '').toLowerCase();
      if (txt.includes('away') && txt.includes('home') && txt.includes('matchup')) {
        processTable(table);
      }
    });
  }

  run();
  setTimeout(run, 150);
  setTimeout(run, 500);
  setTimeout(run, 1000);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
  });

  document.addEventListener('change', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
  });

  document.addEventListener('input', () => {
    setTimeout(run, 300);
  });
})();



(function restoreSplitEdgeBettingContext(){
  function txt(el){ return String(el && el.textContent || '').replace(/\s+/g,' ').trim(); }

  function dash(){ return '<span class="cfb-edge-pill even">—</span>'; }

  function norm(s){ return txt({textContent:s}).toLowerCase(); }

  function splitEdge(edgeHtml, away, home){
    const tmp = document.createElement('div');
    tmp.innerHTML = edgeHtml || '';
    const t = norm(tmp.textContent);

    let awayEdge = dash();
    let homeEdge = dash();

    if (!t || t === '-' || t === '—') return {awayEdge, homeEdge};

    if (t.includes(norm(away))) awayEdge = edgeHtml;
    else if (t.includes(norm(home))) homeEdge = edgeHtml;
    else homeEdge = edgeHtml;

    return {awayEdge, homeEdge};
  }

  function rankClass(n){
    if (!n || Number.isNaN(n)) return 'ctx-rank-neutral';
    if (n <= 35) return 'ctx-rank-good';
    if (n <= 80) return 'ctx-rank-mid';
    return 'ctx-rank-bad';
  }

  function rankChip(rankText){
    const n = Number(String(rankText).replace('#','').trim());
    if (!n || Number.isNaN(n)) return rankText;
    return `<span class="ctx-rank-chip ${rankClass(n)}">${rankText}</span>`;
  }

  function chipRanks(html){
    return String(html || '').replace(/(^|>|\s)(#\d{1,3})(?=\s|<|$)/g, function(match, prefix, rank){
      // avoid double chipping
      if (match.includes('ctx-rank-chip')) return match;
      return `${prefix}${rankChip(rank)}`;
    });
  }

  function process(table){
    if (!table || table.dataset.contextSplitRestored === '1') return;
    if (!table.classList.contains('cfb-context-table')) return;

    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    if (!thead || !tbody) return;

    const headers = Array.from(thead.querySelectorAll('th')).map(th => txt(th));
    if (headers.length < 4) return;

    // Already split or old layout
    let away, home, oldShape = false, splitShape = false;

    if (headers.length >= 5 && /metric/i.test(headers[2])) {
      away = headers[1];
      home = headers[3];
      splitShape = true;
    } else if (/category/i.test(headers[0]) && /edge/i.test(headers[3])) {
      away = headers[1];
      home = headers[2];
      oldShape = true;
    } else {
      return;
    }

    const rows = Array.from(tbody.querySelectorAll('tr')).map(row => {
      const cells = Array.from(row.children);

      let awayEdgeHtml, awayVal, metric, homeVal, homeEdgeHtml;

      if (splitShape && cells.length >= 5) {
        awayEdgeHtml = cells[0].innerHTML;
        awayVal = cells[1].innerHTML;
        metric = cells[2].innerHTML;
        homeVal = cells[3].innerHTML;
        homeEdgeHtml = cells[4].innerHTML;
      } else if (oldShape && cells.length >= 4) {
        metric = cells[0].innerHTML;
        awayVal = cells[1].innerHTML;
        homeVal = cells[2].innerHTML;
        const split = splitEdge(cells[3].innerHTML, away, home);
        awayEdgeHtml = split.awayEdge;
        homeEdgeHtml = split.homeEdge;
      } else {
        return '';
      }

      awayVal = chipRanks(awayVal);
      homeVal = chipRanks(homeVal);

      return `<tr>
        <td class="cfb-edge-cell cfb-context-away-edge">${awayEdgeHtml || dash()}</td>
        <td class="cfb-context-team-val">${awayVal}</td>
        <td class="cfb-context-cat">${metric}</td>
        <td class="cfb-context-team-val">${homeVal}</td>
        <td class="cfb-edge-cell cfb-context-home-edge">${homeEdgeHtml || dash()}</td>
      </tr>`;
    }).join('');

    thead.innerHTML = `<tr>
      <th>${away} Edge<br><span class="cfb-edge-note">- = no edge</span></th>
      <th>${away}</th>
      <th>Metric</th>
      <th>${home}</th>
      <th>${home} Edge<br><span class="cfb-edge-note">- = no edge</span></th>
    </tr>`;

    tbody.innerHTML = rows;
    table.classList.add('cfb-context-split-restored');
    table.dataset.contextSplitRestored = '1';
  }

  function run(){
    document.querySelectorAll('.cfb-context-table').forEach(process);
  }

  run();
  setTimeout(run,100);
  setTimeout(run,500);
  document.addEventListener('click',()=>setTimeout(run,150));
})();



(function fiveFactorsUiCleanup(){
  function clean(s){
    return String(s || '').replace(/\s+/g, ' ').trim();
  }

  function norm(s){
    return clean(s)
      .toLowerCase()
      .replace(/&/g, 'and')
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();
  }

  function properTeamName(raw){
    const key = norm(raw);
    if (typeof DB !== 'undefined' && DB.teams) {
      const hit = DB.teams.find(t => norm(t.team) === key);
      if (hit) return hit.team;
    }

    return clean(raw)
      .toLowerCase()
      .split(' ')
      .map(w => {
        const up = w.toUpperCase();
        if (['USC','UCLA','BYU','SMU','TCU','UTSA','UNLV','UAB','FIU','FAU','LSU','UTEP'].includes(up)) return up;
        return w ? w.charAt(0).toUpperCase() + w.slice(1) : w;
      })
      .join(' ');
  }

  function teamsFromHead(table){
    const head = table.closest('.cfb-side-card')?.querySelector('.cfb-side-head');
    const text = clean(head?.textContent || '');
    const m = text.match(/^(.+?)\s+OFF\s+VS\s+(.+?)\s+DEF$/i);

    if (!m) return {off:'Offense', def:'Defense'};

    return {
      off: properTeamName(m[1]),
      def: properTeamName(m[2])
    };
  }

  function replaceBadgeLabel(pill, fromWord, toTeam){
    const t = clean(pill.textContent);
    const re = new RegExp('^' + fromWord + '\\b', 'i');
    if (re.test(t)) {
      pill.textContent = t.replace(re, toTeam);
    }
  }

  function cleanupFactorTable(table){
    if (!table || !table.classList.contains('cfb-factor-table')) return;

    const teams = teamsFromHead(table);

    // Replace generic Offense/Defense badge labels with actual team names.
    table.querySelectorAll('.cfb-off-edge-col .cfb-edge-pill').forEach(pill => {
      replaceBadgeLabel(pill, 'Offense', teams.off);
    });

    table.querySelectorAll('.cfb-def-edge-col .cfb-edge-pill').forEach(pill => {
      replaceBadgeLabel(pill, 'Defense', teams.def);
    });

    // Keep only the five desired factors.
    table.querySelectorAll('tbody tr').forEach(row => {
      const metric = clean(row.querySelector('.cfb-factor-name')?.textContent || '').toLowerCase();

      if (
        metric.includes('ppa') ||
        metric.includes('front 7') ||
        metric.includes('db havoc')
      ) {
        row.remove();
      }
    });
  }

  function renameTitle(){
    document.querySelectorAll('.cfb-section-title, .section-title, .matchup-panel-title, div').forEach(el => {
      const txt = clean(el.textContent);
      if (/four factors\s*\+\s*havoc matchup/i.test(txt)) {
        // Preserve any secondary note/span if present by changing only first text node when possible.
        for (const node of el.childNodes) {
          if (node.nodeType === Node.TEXT_NODE && /four factors/i.test(node.textContent)) {
            node.textContent = node.textContent.replace(/four factors\s*\+\s*havoc matchup/i, 'Five Factors');
          }
        }
        if (/four factors\s*\+\s*havoc matchup/i.test(clean(el.textContent))) {
          el.textContent = 'Five Factors';
        }
      }
    });
  }

  function run(){
    renameTitle();
    document.querySelectorAll('.cfb-factor-table').forEach(cleanupFactorTable);
  }

  run();
  setTimeout(run, 100);
  setTimeout(run, 400);
  setTimeout(run, 1000);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1000);
  });
})();



(function fixFiveFactorEdgeTeamLabels(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function norm(s){
    return clean(s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  }

  function properTeam(raw){
    const key = norm(raw);
    if (typeof DB !== 'undefined' && DB.teams) {
      const hit = DB.teams.find(t => norm(t.team) === key);
      if (hit) return hit.team;
    }
    return clean(raw);
  }

  function teamsFromTable(table){
    const side = table.closest('.cfb-side-card');
    const head = side && side.querySelector('.cfb-side-head');
    const text = clean(head && head.textContent);
    const m = text.match(/^(.+?)\s+OFF\s+VS\s+(.+?)\s+DEF$/i);
    if (!m) return null;
    return {
      off: properTeam(m[1]),
      def: properTeam(m[2])
    };
  }

  function replaceGeneric(pill, teams){
    const t = clean(pill.textContent);
    if (!t || t === '—' || t === '-') return;

    if (/^offense\b/i.test(t)) {
      pill.textContent = t.replace(/^offense\b/i, teams.off);
    } else if (/^defense\b/i.test(t)) {
      pill.textContent = t.replace(/^defense\b/i, teams.def);
    }
  }

  function run(){
    document.querySelectorAll('.cfb-factor-table').forEach(table => {
      const teams = teamsFromTable(table);
      if (!teams) return;

      table.querySelectorAll('.cfb-edge-pill').forEach(pill => replaceGeneric(pill, teams));
    });
  }

  run();
  setTimeout(run, 100);
  setTimeout(run, 400);
  setTimeout(run, 1000);
  setTimeout(run, 2000);

  document.addEventListener('click', () => {
    setTimeout(run, 100);
    setTimeout(run, 500);
    setTimeout(run, 1200);
  });
})();



(function finalFiveFactorTeamNamePatch(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function norm(s){
    return clean(s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  }

  function siteTeam(raw){
    const key = norm(raw);
    if (typeof DB !== 'undefined' && DB.teams) {
      const hit = DB.teams.find(t => norm(t.team) === key);
      if (hit) return hit.team;
    }
    return clean(raw);
  }

  function titleFromTable(table){
    const card = table.closest('.cfb-side-card');
    if (!card) return '';

    // Prefer the side card header text.
    const head = card.querySelector('.cfb-side-head');
    if (head) {
      const t = clean(head.textContent);
      if (/off\s+vs\s+.*def/i.test(t)) return t;
    }

    // Fallback: search nearby previous siblings/text.
    const all = clean(card.textContent);
    const m = all.match(/([A-Za-z0-9 .&'()-]+?)\s+OFF\s+VS\s+([A-Za-z0-9 .&'()-]+?)\s+DEF/i);
    return m ? `${m[1]} OFF VS ${m[2]} DEF` : '';
  }

  function teams(table){
    const title = titleFromTable(table);
    const m = title.match(/^(.+?)\s+OFF\s+VS\s+(.+?)\s+DEF$/i);
    if (!m) return null;
    return { off: siteTeam(m[1]), def: siteTeam(m[2]) };
  }

  function rewrite(table){
    const t = teams(table);
    if (!t) return;

    table.querySelectorAll('.cfb-off-edge-col .cfb-edge-pill, td:first-child .cfb-edge-pill').forEach(pill => {
      const s = clean(pill.textContent);
      if (/^offense\b/i.test(s)) {
        pill.textContent = s.replace(/^offense\b/i, t.off);
      }
    });

    table.querySelectorAll('.cfb-def-edge-col .cfb-edge-pill, td:last-child .cfb-edge-pill').forEach(pill => {
      const s = clean(pill.textContent);
      if (/^defense\b/i.test(s)) {
        pill.textContent = s.replace(/^defense\b/i, t.def);
      }
    });
  }

  function run(){
    document.querySelectorAll('.cfb-factor-table').forEach(rewrite);
  }

  run();
  setTimeout(run, 100);
  setTimeout(run, 400);
  setTimeout(run, 1000);
  setTimeout(run, 2000);

  document.addEventListener('click', () => {
    setTimeout(run, 100);
    setTimeout(run, 400);
    setTimeout(run, 1000);
  });
})();



(function restoreBettingContextSplitOnly(){
  function clean(s){ return String(s || '').replace(/\s+/g,' ').trim(); }
  function norm(s){ return clean(s).toLowerCase(); }
  function dash(){ return '<span class="cfb-edge-pill even">—</span>'; }

  function splitEdge(edgeHtml, away, home){
    const tmp = document.createElement('div');
    tmp.innerHTML = edgeHtml || '';
    const text = norm(tmp.textContent);

    let awayEdge = dash();
    let homeEdge = dash();

    if (!text || text === '-' || text === '—') return {awayEdge, homeEdge};

    if (text.includes(norm(away))) awayEdge = edgeHtml;
    else if (text.includes(norm(home))) homeEdge = edgeHtml;
    else homeEdge = edgeHtml;

    return {awayEdge, homeEdge};
  }

  function rankClass(n){
    if (!n || Number.isNaN(n)) return 'ctx-rank-neutral';
    if (n <= 35) return 'ctx-rank-good';
    if (n <= 80) return 'ctx-rank-mid';
    return 'ctx-rank-bad';
  }

  function rankChip(rank){
    const n = Number(String(rank).replace('#','').trim());
    if (!n || Number.isNaN(n)) return rank;
    return `<span class="ctx-rank-chip ${rankClass(n)}">${rank}</span>`;
  }

  function chipRanks(html){
    return String(html || '').replace(/(^|>|\s)(#\d{1,3})(?=\s|<|$)/g, function(match, prefix, rank){
      if (match.includes('ctx-rank-chip')) return match;
      return `${prefix}${rankChip(rank)}`;
    });
  }

  function process(table){
    if (!table || table.dataset.bettingContextSplitOnly === '1') return;
    if (!table.classList.contains('cfb-context-table')) return;

    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    if (!thead || !tbody) return;

    const headers = Array.from(thead.querySelectorAll('th')).map(th => clean(th.textContent));

    let away = '';
    let home = '';
    let oldShape = false;
    let splitShape = false;

    if (headers.length >= 5 && /metric/i.test(headers[2])) {
      away = headers[1];
      home = headers[3];
      splitShape = true;
    } else if (headers.length >= 4 && /category/i.test(headers[0]) && /edge/i.test(headers[3])) {
      away = headers[1];
      home = headers[2];
      oldShape = true;
    } else {
      return;
    }

    const rows = Array.from(tbody.querySelectorAll('tr')).map(row => {
      const cells = Array.from(row.children);

      let awayEdgeHtml = dash();
      let awayVal = '';
      let metric = '';
      let homeVal = '';
      let homeEdgeHtml = dash();

      if (splitShape && cells.length >= 5) {
        awayEdgeHtml = cells[0].innerHTML || dash();
        awayVal = cells[1].innerHTML;
        metric = cells[2].innerHTML;
        homeVal = cells[3].innerHTML;
        homeEdgeHtml = cells[4].innerHTML || dash();
      } else if (oldShape && cells.length >= 4) {
        metric = cells[0].innerHTML;
        awayVal = cells[1].innerHTML;
        homeVal = cells[2].innerHTML;
        const split = splitEdge(cells[3].innerHTML, away, home);
        awayEdgeHtml = split.awayEdge;
        homeEdgeHtml = split.homeEdge;
      } else {
        return '';
      }

      return `<tr>
        <td class="cfb-edge-cell cfb-context-away-edge">${awayEdgeHtml}</td>
        <td class="cfb-context-team-val">${chipRanks(awayVal)}</td>
        <td class="cfb-context-cat">${metric}</td>
        <td class="cfb-context-team-val">${chipRanks(homeVal)}</td>
        <td class="cfb-edge-cell cfb-context-home-edge">${homeEdgeHtml}</td>
      </tr>`;
    }).join('');

    thead.innerHTML = `<tr>
      <th>${away} Edge<br><span class="cfb-edge-note">- = no edge</span></th>
      <th>${away}</th>
      <th>Metric</th>
      <th>${home}</th>
      <th>${home} Edge<br><span class="cfb-edge-note">- = no edge</span></th>
    </tr>`;

    tbody.innerHTML = rows;
    table.classList.add('cfb-context-split-restored');
    table.dataset.bettingContextSplitOnly = '1';
  }

  function run(){
    document.querySelectorAll('.cfb-context-table').forEach(process);
  }

  run();
  setTimeout(run, 150);
  setTimeout(run, 500);
  setTimeout(run, 1000);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
  });
})();



(function bettingContextAlignmentSosCleanup(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function rankClass(n){
    if (!n || Number.isNaN(n)) return 'ctx-rank-neutral';
    if (n <= 35) return 'ctx-rank-good';
    if (n <= 80) return 'ctx-rank-mid';
    return 'ctx-rank-bad';
  }

  function rankChip(rankText){
    const n = Number(String(rankText).replace('#','').trim());
    if (!n || Number.isNaN(n)) {
      return `<span class="ctx-rank-chip sos-clean-chip ctx-rank-neutral">—</span>`;
    }
    return `<span class="ctx-rank-chip sos-clean-chip ${rankClass(n)}">${rankText}</span>`;
  }

  function centerRankLines(cell){
    if (!cell || cell.dataset.centerRankLines === '1') return;

    // Only apply to cells that start with a rank chip/text and have subtext.
    const text = clean(cell.textContent);
    if (!/^#\d+/.test(text)) return;

    const firstChip = cell.querySelector('.ctx-rank-chip');
    if (!firstChip) return;

    // Wrap leading chip and any immediate text until first <br> or block into centered line.
    const html = cell.innerHTML;
    const parts = html.split(/<br\s*\/?>/i);

    if (parts.length > 1) {
      const first = parts.shift();
      const rest = parts.join('<br>');
      cell.innerHTML = `<div class="bc-rank-line">${first}</div><span class="bc-sub-line">${rest}</span>`;
    } else {
      cell.innerHTML = `<div class="bc-rank-line">${html}</div>`;
    }

    cell.dataset.centerRankLines = '1';
  }

  function extractRanksFromText(text){
    return clean(text).match(/#\d+/g) || [];
  }

  function formatSosCell(cell){
    if (!cell || cell.dataset.sosCleanV2 === '1') return;

    const raw = clean(cell.textContent);
    if (!raw || !/overall|off test|def test|off avg|def avg|biggest test/i.test(raw)) return;

    const ranks = extractRanksFromText(raw);

    // Existing raw shape usually contains:
    // current/biggest rank, overall avg, overall max, off avg, off max, def avg, def max
    // Or after prior formatters: overall avg/max/current, off avg/max/current, def avg/max/current.
    let current = null;
    let overallAvg = null, overallMax = null;
    let offAvg = null, offMax = null;
    let defAvg = null, defMax = null;

    const biggest = raw.match(/Biggest test vs\s*(#\d+)/i);
    if (biggest) current = biggest[1];

    const overall = raw.match(/Overall avg\s*(#\d+)\s*\/\s*max\s*(#\d+)/i);
    if (overall) {
      overallAvg = overall[1];
      overallMax = overall[2];
    }

    const off = raw.match(/Off test avg\s*(#\d+)\s*\/\s*max\s*(#\d+)/i) || raw.match(/Off avg\s*(#\d+)\s*\/\s*off max\s*(#\d+)/i);
    if (off) {
      offAvg = off[1];
      offMax = off[2];
    }

    const def = raw.match(/Def test avg\s*(#\d+)\s*\/\s*max\s*(#\d+)/i) || raw.match(/Def avg\s*(#\d+)\s*\/\s*def max\s*(#\d+)/i);
    if (def) {
      defAvg = def[1];
      defMax = def[2];
    }

    // Fallback: preserve best known order
    if (!overallAvg && ranks.length >= 2) {
      // if current line exists first, ranks[0] is current, then pairs follow
      if (current && ranks[0] === current && ranks.length >= 7) {
        overallAvg = ranks[1]; overallMax = ranks[2];
        offAvg = ranks[3]; offMax = ranks[4];
        defAvg = ranks[5]; defMax = ranks[6];
      } else if (ranks.length >= 6) {
        overallAvg = ranks[0]; overallMax = ranks[1];
        offAvg = ranks[2]; offMax = ranks[3];
        defAvg = ranks[4]; defMax = ranks[5];
        current = current || ranks[1];
      }
    }

    // If no current rank was parsed, use overall max as a conservative placeholder.
    current = current || overallMax || '—';

    function row(label, avg, max, cur){
      return `<div class="sos-clean-v2-row">
        <span class="sos-clean-v2-label">${label}</span>
        <span class="sos-clean-v2-pair">${rankChip(avg)}${rankChip(max)}</span>
        <span class="sos-clean-v2-arrow">→</span>
        <span>${rankChip(cur)}</span>
      </div>`;
    }

    cell.innerHTML = `<div class="sos-clean-v2">
      ${row('Overall', overallAvg, overallMax, current)}
      ${row('Off', offAvg, offMax, current)}
      ${row('Def', defAvg, defMax, current)}
    </div>`;

    cell.dataset.sosCleanV2 = '1';
  }

  function processContextTable(table){
    if (!table || !table.classList.contains('cfb-context-table')) return;

    table.querySelectorAll('.cfb-context-cat').forEach(metricCell => {
      const metric = clean(metricCell.textContent);
      if (metric === 'SOS / Step') metricCell.textContent = 'SOS';
    });

    table.querySelectorAll('tbody tr').forEach(row => {
      const metric = clean(row.querySelector('.cfb-context-cat')?.textContent || '');

      if (metric === 'SOS' || metric === 'SOS / Step') {
        row.querySelectorAll('.cfb-context-team-val').forEach(formatSosCell);
      } else {
        row.querySelectorAll('.cfb-context-team-val').forEach(centerRankLines);
      }
    });
  }

  function run(){
    document.querySelectorAll('.cfb-context-table').forEach(processContextTable);
  }

  run();
  setTimeout(run, 150);
  setTimeout(run, 500);
  setTimeout(run, 1000);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1000);
  });
})();



(function luckSosLabelTweak(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function fixLuckRows(){
    document.querySelectorAll('.cfb-context-table tbody tr').forEach(row => {
      const metric = clean(row.querySelector('.cfb-context-cat')?.textContent || '');
      if (metric !== 'Luck Rating') return;

      row.querySelectorAll('.cfb-context-team-val').forEach(cell => {
        if (cell.dataset.luckLegendFixed === '1') return;

        const html = cell.innerHTML;

        // Replace the inline "+ = lucky / - = unlucky" with stacked lines.
        const fixed = html
          .replace(/\+\s*=\s*lucky\s*\/\s*-\s*=\s*unlucky/gi,
            '<span class="luck-legend-stack">+ = lucky<br>- = unlucky</span>')
          .replace(/\+\s*=\s*lucky\s*\/\s*−\s*=\s*unlucky/gi,
            '<span class="luck-legend-stack">+ = lucky<br>- = unlucky</span>');

        cell.innerHTML = fixed;
        cell.dataset.luckLegendFixed = '1';
      });
    });
  }

  function fixSosHeaders(){
    document.querySelectorAll('.sos-clean-v2').forEach(box => {
      if (box.dataset.sosHeadersFixed === '1') return;

      const head = document.createElement('div');
      head.className = 'sos-clean-v2-head';
      head.innerHTML = `
        <span></span>
        <span>Avg</span>
        <span>Max</span>
        <span></span>
        <span>Current</span>
      `;

      box.insertBefore(head, box.firstChild);
      box.dataset.sosHeadersFixed = '1';
    });
  }

  function run(){
    fixLuckRows();
    fixSosHeaders();
  }

  run();
  setTimeout(run, 150);
  setTimeout(run, 500);
  setTimeout(run, 1000);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1000);
  });
})();



(function fixSosCurrentOpponentRanks(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function norm(s){
    return clean(s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  }

  function rankClass(n){
    if (!n || Number.isNaN(n)) return 'ctx-rank-neutral';
    if (n <= 35) return 'ctx-rank-good';
    if (n <= 80) return 'ctx-rank-mid';
    return 'ctx-rank-bad';
  }

  function chip(n){
    if (!n || Number.isNaN(Number(n))) {
      return `<span class="ctx-rank-chip sos-clean-chip ctx-rank-neutral">—</span>`;
    }
    const r = Math.round(Number(n));
    return `<span class="ctx-rank-chip sos-clean-chip ${rankClass(r)}">#${r}</span>`;
  }

  function teamObj(teamName){
    if (typeof DB === 'undefined' || !DB.teams) return null;
    const key = norm(teamName);
    return DB.teams.find(t => norm(t.team) === key) || null;
  }

  function offenseRank(teamName){
    if (typeof DB === 'undefined' || !DB.teams) return null;
    const key = norm(teamName);
    const sorted = DB.teams
      .filter(t => t.sp_offense != null && isFinite(Number(t.sp_offense)))
      .slice()
      .sort((a,b) => Number(b.sp_offense) - Number(a.sp_offense));
    const idx = sorted.findIndex(t => norm(t.team) === key);
    return idx >= 0 ? idx + 1 : null;
  }

  function defenseRank(teamName){
    if (typeof DB === 'undefined' || !DB.teams) return null;
    const key = norm(teamName);
    const sorted = DB.teams
      .filter(t => t.sp_defense != null && isFinite(Number(t.sp_defense)))
      .slice()
      .sort((a,b) => Number(a.sp_defense) - Number(b.sp_defense));
    const idx = sorted.findIndex(t => norm(t.team) === key);
    return idx >= 0 ? idx + 1 : null;
  }

  function overallRank(teamName){
    const t = teamObj(teamName);
    return t && t.rank != null ? Number(t.rank) : null;
  }

  function teamsFromContextTable(table){
    const ths = Array.from(table.querySelectorAll('thead th')).map(th => clean(th.textContent));

    // Split Betting Context layout:
    // Away Edge | Away | Metric | Home | Home Edge
    if (ths.length >= 5 && /metric/i.test(ths[2])) {
      return { away: ths[1], home: ths[3] };
    }

    // Old fallback:
    // Category | Away | Home | Edge
    if (ths.length >= 4) {
      return { away: ths[1], home: ths[2] };
    }

    return { away:'', home:'' };
  }

  function opponentForValueCell(row, cell, table){
    const teams = teamsFromContextTable(table);
    const cells = Array.from(row.children);
    const idx = cells.indexOf(cell);

    // In split layout: index 1 = away team value, index 3 = home team value
    if (idx === 1) return teams.home;
    if (idx === 3) return teams.away;

    return '';
  }

  function fixCell(row, cell, table){
    const opp = opponentForValueCell(row, cell, table);
    if (!opp) return;

    const ranks = {
      overall: overallRank(opp),
      off: offenseRank(opp),
      def: defenseRank(opp)
    };

    cell.querySelectorAll('.sos-clean-v2-row').forEach(line => {
      const label = clean(line.querySelector('.sos-clean-v2-label')?.textContent || '').toLowerCase();

      let wanted = null;
      if (label.includes('overall')) wanted = ranks.overall;
      else if (label === 'off' || label.includes('off')) wanted = ranks.off;
      else if (label === 'def' || label.includes('def')) wanted = ranks.def;

      if (!wanted) return;

      // Replace only the chip after the arrow; leave avg/max chips untouched.
      const arrow = line.querySelector('.sos-clean-v2-arrow');
      if (!arrow) return;

      let currentWrap = arrow.nextElementSibling;
      if (!currentWrap) return;

      currentWrap.innerHTML = chip(wanted);
    });
  }

  function run(){
    document.querySelectorAll('.cfb-context-table tbody tr').forEach(row => {
      const metric = clean(row.querySelector('.cfb-context-cat')?.textContent || '');
      if (metric !== 'SOS') return;

      const table = row.closest('.cfb-context-table');
      row.querySelectorAll('.cfb-context-team-val').forEach(cell => {
        fixCell(row, cell, table);
      });
    });
  }

  run();
  setTimeout(run, 150);
  setTimeout(run, 500);
  setTimeout(run, 1000);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1000);
  });
})();



(function projectedTeamPointsHeader(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function norm(s){
    return clean(s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  }

  function parseProjection(text){
    // Example: "Ohio State -6.5 · Total 51.4"
    const t = clean(text);

    const totalMatch = t.match(/total\s+([0-9]+(?:\.[0-9]+)?)/i);
    if (!totalMatch) return null;

    const total = Number(totalMatch[1]);

    const spreadMatch = t.match(/^(.+?)\s+(-|\+)?([0-9]+(?:\.[0-9]+)?)/);
    if (!spreadMatch) return null;

    const favTeam = clean(spreadMatch[1]);
    const sign = spreadMatch[2] || "-";
    const spreadVal = Number(spreadMatch[3]);

    // If displayed as +, then the named team is dog; if -, named team is favorite.
    const namedIsFavorite = sign !== "+";
    const absSpread = Math.abs(spreadVal);

    return { total, favTeam, namedIsFavorite, absSpread };
  }

  function addPoints(header){
    if (!header || header.dataset.projectedPointsDone === '1') return;

    const center = header.querySelector('.cfb-game-proj');
    const projection = parseProjection(center && center.textContent);
    if (!projection) return;

    const teamHeads = Array.from(header.querySelectorAll('.cfb-team-head'));
    if (teamHeads.length < 2) return;

    const teams = teamHeads.map(h => clean(h.querySelector('.cfb-team-name')?.textContent || ''));
    if (teams.length < 2 || !teams[0] || !teams[1]) return;

    const teamA = teams[0];
    const teamB = teams[1];

    const named = projection.favTeam;
    const namedNorm = norm(named);

    let favorite = '';
    let dog = '';

    const namedMatchesA = norm(teamA) === namedNorm || norm(teamA).includes(namedNorm) || namedNorm.includes(norm(teamA));
    const namedMatchesB = norm(teamB) === namedNorm || norm(teamB).includes(namedNorm) || namedNorm.includes(norm(teamB));

    if (projection.namedIsFavorite) {
      if (namedMatchesA) { favorite = teamA; dog = teamB; }
      else if (namedMatchesB) { favorite = teamB; dog = teamA; }
    } else {
      if (namedMatchesA) { dog = teamA; favorite = teamB; }
      else if (namedMatchesB) { dog = teamB; favorite = teamA; }
    }

    if (!favorite || !dog) return;

    const favPts = (projection.total + projection.absSpread) / 2;
    const dogPts = (projection.total - projection.absSpread) / 2;

    const pointMap = {};
    pointMap[favorite] = favPts;
    pointMap[dog] = dogPts;

    teamHeads.forEach(h => {
      const nameEl = h.querySelector('.cfb-team-name');
      const team = clean(nameEl && nameEl.textContent);
      if (!nameEl || pointMap[team] == null) return;

      // Remove old if rerun.
      h.querySelectorAll('.cfb-team-proj-points').forEach(x => x.remove());

      const pts = Number(pointMap[team]).toFixed(1);
      const chip = document.createElement('span');
      chip.className = 'cfb-team-proj-points';
      chip.textContent = `${pts} pts`;

      if (h.classList.contains('home')) {
        nameEl.insertAdjacentElement('afterend', chip);
      } else {
        nameEl.insertAdjacentElement('afterend', chip);
      }
    });

    header.dataset.projectedPointsDone = '1';
  }

  function run(){
    document.querySelectorAll('.cfb-matchup-header').forEach(addPoints);
  }

  run();
  setTimeout(run, 150);
  setTimeout(run, 500);
  setTimeout(run, 1000);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1000);
  });
})();



(function corePowerRankChips(){
  function rankClass(n){
    if (!n || Number.isNaN(n)) return 'core-rank-neutral';
    if (n <= 35) return 'core-rank-good';
    if (n <= 80) return 'core-rank-mid';
    return 'core-rank-bad';
  }

  function chip(rankText){
    const n = Number(String(rankText).replace('#','').trim());
    if (!n || Number.isNaN(n)) return rankText;
    return `<span class="core-rank-chip ${rankClass(n)}">${rankText}</span>`;
  }

  function apply(el){
    if (!el || el.dataset.coreRankChips === '1') return;

    el.innerHTML = el.innerHTML.replace(/(^|>|\s)(#\d{1,3})(?=\s|<|$)/g, function(match, prefix, rank){
      if (match.includes('core-rank-chip')) return match;
      return `${prefix}${chip(rank)}`;
    });

    el.dataset.coreRankChips = '1';
  }

  function run(){
    document.querySelectorAll('.cfb-power-card').forEach(card => {
      card.querySelectorAll('.cfb-power-team, .cfb-power-val, .cfb-power-row, div').forEach(apply);
    });
  }

  run();
  setTimeout(run, 150);
  setTimeout(run, 500);
  setTimeout(run, 1000);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1000);
  });
})();



(function globalMatchupUiConsistency(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function norm(s){
    return clean(s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  }

  function rankClass(n){
    if (!n || Number.isNaN(n)) return 'core-rank-neutral';
    if (n <= 35) return 'core-rank-good';
    if (n <= 80) return 'core-rank-mid';
    return 'core-rank-bad';
  }

  function rankChip(rankText){
    const n = Number(String(rankText).replace('#','').trim());
    if (!n || Number.isNaN(n)) return rankText;
    return `<span class="core-rank-chip ${rankClass(n)}">${rankText}</span>`;
  }

  function chipCoreRanks(panel){
    if (!panel) return;

    panel.querySelectorAll('.cfb-power-card').forEach(card => {
      if (card.dataset.globalRankChips === '1') return;

      card.innerHTML = card.innerHTML.replace(/(^|>|\s)(#\d{1,3})(?=\s|<|$)/g, function(match, prefix, rank){
        if (match.includes('core-rank-chip')) return match;
        return `${prefix}${rankChip(rank)}`;
      });

      card.dataset.globalRankChips = '1';
    });
  }

  function parseProjection(panel){
    const text = clean(panel.querySelector('.cfb-game-proj')?.textContent || '');
    if (!text) return null;

    const totalMatch = text.match(/total\s+([0-9]+(?:\.[0-9]+)?)/i);
    const spreadMatch = text.match(/^(.+?)\s+(-|\+)?([0-9]+(?:\.[0-9]+)?)/);

    if (!totalMatch || !spreadMatch) return null;

    return {
      total: Number(totalMatch[1]),
      namedTeam: clean(spreadMatch[1]),
      sign: spreadMatch[2] || '-',
      spread: Math.abs(Number(spreadMatch[3]))
    };
  }

  function addProjectedPoints(panel){
    if (!panel || panel.dataset.globalProjectedPoints === '1') return;

    const proj = parseProjection(panel);
    if (!proj) return;

    const heads = Array.from(panel.querySelectorAll('.cfb-team-head'));
    if (heads.length < 2) return;

    const teams = heads.map(h => clean(h.querySelector('.cfb-team-name')?.textContent || ''));
    if (!teams[0] || !teams[1]) return;

    const namedNorm = norm(proj.namedTeam);
    let favorite = '';
    let dog = '';

    for (const team of teams) {
      const tn = norm(team);
      const match = tn === namedNorm || tn.includes(namedNorm) || namedNorm.includes(tn);
      if (!match) continue;

      if (proj.sign === '+') {
        dog = team;
        favorite = teams.find(x => x !== team);
      } else {
        favorite = team;
        dog = teams.find(x => x !== team);
      }
    }

    if (!favorite || !dog) return;

    const favPts = (proj.total + proj.spread) / 2;
    const dogPts = (proj.total - proj.spread) / 2;
    const pts = {};
    pts[favorite] = favPts;
    pts[dog] = dogPts;

    heads.forEach(h => {
      const nameEl = h.querySelector('.cfb-team-name');
      const team = clean(nameEl?.textContent || '');
      if (!nameEl || pts[team] == null) return;

      h.querySelectorAll('.cfb-team-proj-points').forEach(x => x.remove());

      const chip = document.createElement('span');
      chip.className = 'cfb-team-proj-points';
      chip.textContent = `${Number(pts[team]).toFixed(1)} pts`;

      if (h.classList.contains('home')) {
        nameEl.parentElement.insertBefore(chip, nameEl);
      } else {
        nameEl.insertAdjacentElement('afterend', chip);
      }
    });

    panel.dataset.globalProjectedPoints = '1';
  }

  function processPanel(panel){
    addProjectedPoints(panel);
    chipCoreRanks(panel);
  }

  function run(){
    document.querySelectorAll('.cfb-matchup-shell, .matchup-panel').forEach(processPanel);
  }

  run();
  setTimeout(run, 150);
  setTimeout(run, 500);
  setTimeout(run, 1000);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1000);
  });
})();



(function syncSeasonScheduleMatchupUi(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function norm(s){
    return clean(s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  }

  function rankClass(n){
    if (!n || Number.isNaN(n)) return 'core-rank-neutral';
    if (n <= 35) return 'core-rank-good';
    if (n <= 80) return 'core-rank-mid';
    return 'core-rank-bad';
  }

  function rankChip(rankText){
    const n = Number(String(rankText).replace('#','').trim());
    if (!n || Number.isNaN(n)) return rankText;
    return `<span class="core-rank-chip ${rankClass(n)}">${rankText}</span>`;
  }

  function parseProjection(panel){
    const text = clean(panel.querySelector('.cfb-game-proj')?.textContent || '');
    if (!text) return null;

    const totalMatch = text.match(/total\s+([0-9]+(?:\.[0-9]+)?)/i);
    const spreadMatch = text.match(/^(.+?)\s+(-|\+)?([0-9]+(?:\.[0-9]+)?)/);

    if (!totalMatch || !spreadMatch) return null;

    return {
      total: Number(totalMatch[1]),
      namedTeam: clean(spreadMatch[1]),
      sign: spreadMatch[2] || '-',
      spread: Math.abs(Number(spreadMatch[3]))
    };
  }

  function addProjectedPoints(panel){
    const proj = parseProjection(panel);
    if (!proj) return;

    const heads = Array.from(panel.querySelectorAll('.cfb-team-head'));
    if (heads.length < 2) return;

    const teams = heads.map(h => clean(h.querySelector('.cfb-team-name')?.textContent || ''));
    if (!teams[0] || !teams[1]) return;

    const namedNorm = norm(proj.namedTeam);
    let favorite = '';
    let dog = '';

    for (const team of teams) {
      const tn = norm(team);
      const match = tn === namedNorm || tn.includes(namedNorm) || namedNorm.includes(tn);
      if (!match) continue;

      if (proj.sign === '+') {
        dog = team;
        favorite = teams.find(x => x !== team);
      } else {
        favorite = team;
        dog = teams.find(x => x !== team);
      }
    }

    if (!favorite || !dog) return;

    const favPts = (proj.total + proj.spread) / 2;
    const dogPts = (proj.total - proj.spread) / 2;

    const pts = {};
    pts[favorite] = favPts;
    pts[dog] = dogPts;

    heads.forEach(h => {
      const nameEl = h.querySelector('.cfb-team-name');
      const team = clean(nameEl?.textContent || '');
      if (!nameEl || pts[team] == null) return;

      h.querySelectorAll('.cfb-team-proj-points').forEach(x => x.remove());

      const chip = document.createElement('span');
      chip.className = 'cfb-team-proj-points';
      chip.textContent = `${Number(pts[team]).toFixed(1)} pts`;

      if (h.classList.contains('home')) {
        nameEl.parentElement.insertBefore(chip, nameEl);
      } else {
        nameEl.insertAdjacentElement('afterend', chip);
      }
    });
  }

  function chipCoreRanks(panel){
    panel.querySelectorAll('.cfb-power-card').forEach(card => {
      // Replace only plain #rank text, not existing chip text.
      card.querySelectorAll('*').forEach(el => {
        if (el.classList && el.classList.contains('core-rank-chip')) return;
        if (!el.childNodes || !el.childNodes.length) return;

        el.childNodes.forEach(node => {
          if (node.nodeType !== Node.TEXT_NODE) return;
          const txt = node.nodeValue;
          if (!/#\d{1,3}/.test(txt)) return;

          const span = document.createElement('span');
          span.innerHTML = txt.replace(/#\d{1,3}/g, m => rankChip(m));
          node.replaceWith(...Array.from(span.childNodes));
        });
      });
    });
  }

  function processPanel(panel){
    if (!panel) return;
    addProjectedPoints(panel);
    chipCoreRanks(panel);
  }

  function run(){
    // Target both schedule detail panels and any cfb matchup shell that appears late.
    document.querySelectorAll('.matchup-detail-row .matchup-panel, .matchup-detail-row .cfb-matchup-shell, .matchup-panel, .cfb-matchup-shell').forEach(processPanel);
  }

  run();
  setTimeout(run, 150);
  setTimeout(run, 500);
  setTimeout(run, 1000);
  setTimeout(run, 1800);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1000);
    setTimeout(run, 1800);
  });

  document.addEventListener('change', () => {
    setTimeout(run, 250);
    setTimeout(run, 900);
  });
})();



(function scheduleMatchupExpandTimingFix(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function norm(s){
    return clean(s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  }

  function rankClass(n){
    if (!n || Number.isNaN(n)) return 'core-rank-neutral';
    if (n <= 35) return 'core-rank-good';
    if (n <= 80) return 'core-rank-mid';
    return 'core-rank-bad';
  }

  function rankChip(rankText){
    const n = Number(String(rankText).replace('#','').trim());
    if (!n || Number.isNaN(n)) return rankText;
    return `<span class="core-rank-chip ${rankClass(n)}">${rankText}</span>`;
  }

  function chipCoreRanks(panel){
    panel.querySelectorAll('.cfb-power-card').forEach(card => {
      card.querySelectorAll('*').forEach(el => {
        if (el.classList && el.classList.contains('core-rank-chip')) return;
        if (!el.childNodes || !el.childNodes.length) return;

        Array.from(el.childNodes).forEach(node => {
          if (node.nodeType !== Node.TEXT_NODE) return;
          const txt = node.nodeValue;
          if (!/#\d{1,3}/.test(txt)) return;

          const span = document.createElement('span');
          span.innerHTML = txt.replace(/#\d{1,3}/g, m => rankChip(m));
          node.replaceWith(...Array.from(span.childNodes));
        });
      });
    });
  }

  function parseProjection(panel){
    const text = clean(panel.querySelector('.cfb-game-proj')?.textContent || '');
    if (!text) return null;

    const totalMatch = text.match(/total\s+([0-9]+(?:\.[0-9]+)?)/i);
    const spreadMatch = text.match(/^(.+?)\s+(-|\+)?([0-9]+(?:\.[0-9]+)?)/);

    if (!totalMatch || !spreadMatch) return null;

    return {
      total: Number(totalMatch[1]),
      namedTeam: clean(spreadMatch[1]),
      sign: spreadMatch[2] || '-',
      spread: Math.abs(Number(spreadMatch[3]))
    };
  }

  function addProjectedPoints(panel){
    const proj = parseProjection(panel);
    if (!proj) return;

    const heads = Array.from(panel.querySelectorAll('.cfb-team-head'));
    if (heads.length < 2) return;

    const teams = heads.map(h => clean(h.querySelector('.cfb-team-name')?.textContent || ''));
    if (!teams[0] || !teams[1]) return;

    const namedNorm = norm(proj.namedTeam);
    let favorite = '';
    let dog = '';

    for (const team of teams) {
      const tn = norm(team);
      const match = tn === namedNorm || tn.includes(namedNorm) || namedNorm.includes(tn);
      if (!match) continue;

      if (proj.sign === '+') {
        dog = team;
        favorite = teams.find(x => x !== team);
      } else {
        favorite = team;
        dog = teams.find(x => x !== team);
      }
    }

    if (!favorite || !dog) return;

    const favPts = (proj.total + proj.spread) / 2;
    const dogPts = (proj.total - proj.spread) / 2;

    const pts = {};
    pts[favorite] = favPts;
    pts[dog] = dogPts;

    heads.forEach(h => {
      const nameEl = h.querySelector('.cfb-team-name');
      const team = clean(nameEl?.textContent || '');
      if (!nameEl || pts[team] == null) return;

      h.querySelectorAll('.cfb-team-proj-points').forEach(x => x.remove());

      const chip = document.createElement('span');
      chip.className = 'cfb-team-proj-points';
      chip.textContent = `${Number(pts[team]).toFixed(1)} pts`;

      if (h.classList.contains('home')) {
        nameEl.parentElement.insertBefore(chip, nameEl);
      } else {
        nameEl.insertAdjacentElement('afterend', chip);
      }
    });
  }

  function polish(){
    document.querySelectorAll('.matchup-detail-row .matchup-panel, .matchup-detail-row .cfb-matchup-shell, .matchup-panel, .cfb-matchup-shell').forEach(panel => {
      addProjectedPoints(panel);
      chipCoreRanks(panel);
    });
  }

  function schedulePolish(){
    [50, 150, 300, 600, 1000, 1600, 2400].forEach(ms => {
      setTimeout(polish, ms);
    });
  }

  document.addEventListener('click', function(e){
    const txt = clean(e.target && e.target.textContent);
    const isMatchupClick =
      e.target.closest('.matchup-toggle') ||
      /matchup/i.test(txt) ||
      e.target.closest('.matchup-detail-row') ||
      e.target.closest('.matchup-panel');

    if (isMatchupClick) schedulePolish();
  });

  // Initial pass for already-open panels
  schedulePolish();
})();
